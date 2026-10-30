"""Development bridge: existing game TCP -> outbound relay channels.

Account token is read from PF_ACCOUNT_TOKEN, never command-line arguments.
The native Android/Windows GUI does not invoke this bridge yet.
"""
import argparse
import asyncio
import ipaddress
import json
import os
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request


def local_host(host):
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def request_api(service, token, operation, data):
    parsed = urllib.parse.urlsplit(service)
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError('Service URL must not contain credentials, query or fragment')
    if parsed.scheme != 'https' and not (parsed.scheme == 'http' and local_host(parsed.hostname or '')):
        raise ValueError('Remote account service requires HTTPS')
    request = urllib.request.Request(service.rstrip('/') + '/v1/' + operation,
        data=json.dumps(data).encode(),
        headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'})
    # Disable redirects: bearer tokens must never be forwarded to another endpoint.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None
    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=10) as response:
            body = response.read(8193)
        if len(body) > 8192:
            raise ValueError('Account service response exceeds limit')
        data = json.loads(body)
    except urllib.error.HTTPError as error:
        status = error.code
        error.close()
        raise ConnectionError('Account service returned HTTP %s' % status) from None
    return data


def request_ticket(service, token, room, role, invite=None):
    return request_api(service, token, 'relay-ticket', {'room': room, 'role': role, 'invite': invite})['ticket']


async def open_channel(args, token, role):
    ticket = await asyncio.to_thread(request_ticket, args.service, token, args.room, role, getattr(args, 'invite', None))
    if args.plain_local_only:
        if not local_host(args.relay_host):
            raise ValueError('Plain transport is allowed only to a literal loopback address')
        context = None
    else:
        context = ssl.create_default_context()
    reader, writer = await asyncio.wait_for(asyncio.open_connection(
        args.relay_host, args.relay_port, ssl=context, limit=65536), timeout=10)
    try:
        writer.write(json.dumps({'ticket': ticket}).encode() + b'\n')
        await writer.drain()
        response = await asyncio.wait_for(reader.readuntil(b'\n'), timeout=65)
        if len(response) > 1024 or json.loads(response).get('status') != 'paired':
            raise ConnectionError('Relay refused channel')
        return reader, writer
    except BaseException:
        writer.close()
        await writer.wait_closed()
        raise


async def bridge(first, second):
    async def copy(reader, writer):
        while True:
            data = await asyncio.wait_for(reader.read(16384), timeout=60)
            if not data:
                return
            writer.write(data)
            await asyncio.wait_for(writer.drain(), timeout=10)
    tasks = [asyncio.create_task(copy(first[0], second[1])),
             asyncio.create_task(copy(second[0], first[1]))]
    try:
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
    finally:
        for _, writer in (first, second):
            writer.close()
        await asyncio.gather(*(writer.wait_closed() for _, writer in (first, second)), return_exceptions=True)


async def run(args, token):
    if args.mode == 'host':
        async def channel():
            failed = False
            while True:
                remote = None
                try:
                    remote = await open_channel(args, token, 'host')
                    failed = False
                    local = await asyncio.wait_for(asyncio.open_connection('127.0.0.1', args.game_port), timeout=5)
                    await bridge(remote, local)
                except (OSError, ValueError, TimeoutError, ConnectionError):
                    if not failed:
                        print('Relay channel failed: check session, room heartbeat, local room and TLS.', file=sys.stderr)
                        failed = True
                    if remote:
                        remote[1].close()
                        await remote[1].wait_closed()
                    await asyncio.sleep(1)
        print('Host relay channels:', args.channels, flush=True)
        async def heartbeat():
            while True:
                await asyncio.to_thread(request_api,args.service,token,'heartbeat-room',{'room':args.room})
                await asyncio.sleep(25)
        tasks=[asyncio.create_task(channel()) for _ in range(args.channels)]
        tasks.append(asyncio.create_task(heartbeat()))
        try:
            await asyncio.gather(*tasks)
        finally:
            for task in tasks:task.cancel()
            await asyncio.gather(*tasks,return_exceptions=True)
    else:
        semaphore = asyncio.Semaphore(1)
        async def joined(reader, writer):
            if semaphore.locked():
                writer.close()
                await writer.wait_closed()
                return
            async with semaphore:
                try:
                    remote = await open_channel(args, token, 'join')
                    await bridge((reader, writer), remote)
                except (OSError, ValueError, TimeoutError, ConnectionError):
                    print('Could not join relay: check session, room, host availability and TLS.', file=sys.stderr)
                    writer.close()
                    await writer.wait_closed()
        server = await asyncio.start_server(joined, '127.0.0.1', args.game_port)
        print('Game joins local TCP endpoint:', server.sockets[0].getsockname(), flush=True)
        async with server:
            await server.serve_forever()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['host', 'join'], required=True)
    parser.add_argument('--service', required=True)
    parser.add_argument('--room', required=True)
    parser.add_argument('--relay-host', required=True)
    parser.add_argument('--relay-port', type=int, required=True)
    parser.add_argument('--game-port', type=int, default=12345)
    parser.add_argument('--channels', type=int, choices=range(1, 8), default=7)
    parser.add_argument('--plain-local-only', action='store_true')
    arguments = parser.parse_args()
    arguments.invite=os.environ.get('PF_ROOM_INVITE')
    secret = os.environ.get('PF_ACCOUNT_TOKEN')
    if not secret:
        parser.error('Set PF_ACCOUNT_TOKEN in this process environment')
    try:
        asyncio.run(run(arguments, secret))
    except KeyboardInterrupt:
        pass

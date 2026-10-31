"""Static proof of DBZ's [MU] branch. Never loads or executes the source PE."""
import hashlib,json
from pathlib import Path
import capstone,pefile
ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    source=ROOT/'../games/DBZ-0.6.9/DBZ LF2 v0.6.9.exe';raw=source.read_bytes()
    digest=hashlib.sha256(raw).hexdigest()
    assert digest=='65f997c3fda7f2a9df200d312a6a74488ae010050b499ef91b6a9c17c048998b'
    pe=pefile.PE(data=raw,fast_load=True)
    assert pe.OPTIONAL_HEADER.ImageBase==0x400000
    code=pe.get_data(0x2029,0x20)
    assert code[:6]==bytes.fromhex('813f5b4d555d')
    decoder=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
    functions={}
    for address,size in ((0x402000,0xdc),(0x401d30,0x61),(0x4020b0,0x2c)):
        data=pe.get_data(address-0x400000,size)
        functions[hex(address)]={'sha256':hashlib.sha256(data).hexdigest(),
            'disassembly':[hex(i.address)+' '+i.mnemonic+' '+i.op_str for i in decoder.disasm(data,address)]}
    report={'source_sha256':digest,'method':'static PE read/disassembly only; no original instructions executed',
            'semantics':'0x402029 compares [MU], 0x402031 calls stop/seek-zero; differing track invokes 0x401d30 releasing COM interfaces; 0x40203f compares [MU] again and skips file loading. Final Run is guarded by a non-null interface, so [MU] leaves music stopped.',
            'functions':functions,'scope':'music control only; mirror fighter selectors are separate and remain unported'}
    (ROOT/'content-packs/dbz/music-sentinel-proof.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Verified static [MU] stop/unload branches; original PE not executed')

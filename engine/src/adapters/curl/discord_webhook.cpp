// SPDX-License-Identifier: MIT
// Copyright (c) 2026 OpenLF2 contributors

#include "openlf2/ports/discord_webhook.hpp"
#include "openlf2/ports/download.hpp"
#include "openlf2/core/json.hpp"
#include "letsencrypt_roots.hpp"
#include <curl/curl.h>
#include <memory>
#include <string>

namespace openlf2 {
namespace {
struct Session {
    CURLcode status = curl_global_init(CURL_GLOBAL_DEFAULT);
    ~Session() { if (status == CURLE_OK) curl_global_cleanup(); }
};
std::size_t discard(char*, std::size_t size, std::size_t count, void*) noexcept {
    // Discord replies 204 (or a small JSON body on error); nothing here is used.
    return size * count;
}
std::string content_json(std::string_view content) {
    ScriptValue value{ScriptTable{{ScriptKey(std::string("content")), ScriptValue{std::string(content)}}}};
    auto text = write_json(value);
    return text ? *text : std::string("{}");
}
bool is_webhook_url(const std::string& address, CURLU* url) {
    const auto part = [&](CURLUPart component) {
        char* text = nullptr;
        std::string result;
        if (curl_url_get(url, component, &text, 0) == CURLUE_OK) { result = text; curl_free(text); }
        return result;
    };
    const auto scheme = part(CURLUPART_SCHEME);
    const auto host = part(CURLUPART_HOST);
    const auto path = part(CURLUPART_PATH);
    if (scheme != "https") return false;
    if (host != "discord.com" && host != "discordapp.com") return false;
    if (path.rfind("/api/webhooks/", 0) != 0) return false;
    // No embedded credentials, query string or fragment -- the token lives only in the path.
    if (!part(CURLUPART_USER).empty() || !part(CURLUPART_PASSWORD).empty()) return false;
    if (address.find_first_of("#") != std::string::npos) return false;
    return true;
}
}

Result<void> send_discord_webhook(std::string_view webhook_url, std::string_view content,
                                  const std::optional<DiscordAttachment>& attachment) {
    static const Session session;
    if (session.status != CURLE_OK) return fail(ErrorCode::dependency, "Discord webhook HTTP unavailable");
    if (webhook_url.size() > 512 || content.size() > 4096)
        return fail(ErrorCode::limit, "Discord webhook request exceeds limit");
    const auto address = std::string(webhook_url);
    std::unique_ptr<CURLU, decltype(&curl_url_cleanup)> url(curl_url(), curl_url_cleanup);
    if (!url || curl_url_set(url.get(), CURLUPART_URL, address.c_str(), 0) != CURLUE_OK)
        return fail(ErrorCode::format, "Invalid Discord webhook URL");
    if (!is_webhook_url(address, url.get()))
        return fail(ErrorCode::format, "Not a Discord webhook URL (https://discord.com/api/webhooks/...)");

    std::unique_ptr<CURL, decltype(&curl_easy_cleanup)> handle(curl_easy_init(), curl_easy_cleanup);
    if (!handle) return fail(ErrorCode::dependency, "Discord webhook HTTP unavailable");

#ifdef __ANDROID__
    static const Result<std::string> ca_bundle = android_system_ca_bundle();
    if (!ca_bundle) return fail(ErrorCode::dependency, "Android CA certificates unavailable");
    curl_blob certificates{const_cast<char*>(ca_bundle->data()), ca_bundle->size(), CURL_BLOB_NOCOPY};
    curl_easy_setopt(handle.get(), CURLOPT_CAINFO_BLOB, &certificates);
#elif defined(_WIN32)
    curl_blob certificates{const_cast<char*>(letsencrypt_roots_pem), sizeof(letsencrypt_roots_pem) - 1, CURL_BLOB_NOCOPY};
    curl_easy_setopt(handle.get(), CURLOPT_CAINFO_BLOB, &certificates);
#endif
#if (defined(_WIN32) || defined(__APPLE__)) && defined(CURLSSLOPT_NATIVE_CA)
    curl_easy_setopt(handle.get(), CURLOPT_SSL_OPTIONS, static_cast<long>(CURLSSLOPT_NATIVE_CA));
#endif
    char error_text[CURL_ERROR_SIZE]{};
    curl_easy_setopt(handle.get(), CURLOPT_ERRORBUFFER, error_text);
    curl_easy_setopt(handle.get(), CURLOPT_URL, address.c_str());
    curl_easy_setopt(handle.get(), CURLOPT_CONNECTTIMEOUT, 10L);
    curl_easy_setopt(handle.get(), CURLOPT_TIMEOUT, 25L);
    curl_easy_setopt(handle.get(), CURLOPT_NOSIGNAL, 1L);
    curl_easy_setopt(handle.get(), CURLOPT_FOLLOWLOCATION, 0L);
    curl_easy_setopt(handle.get(), CURLOPT_WRITEFUNCTION, discard);

    std::unique_ptr<curl_mime, decltype(&curl_mime_free)> mime(nullptr, curl_mime_free);
    std::string body;
    std::unique_ptr<curl_slist, decltype(&curl_slist_free_all)> headers(nullptr, curl_slist_free_all);
    if (attachment) {
        mime.reset(curl_mime_init(handle.get()));
        if (!mime) return fail(ErrorCode::limit, "Discord webhook attachment allocation failed");
        curl_mimepart* json_part = curl_mime_addpart(mime.get());
        const auto payload = content_json(content);
        curl_mime_data(json_part, payload.data(), payload.size());
        curl_mime_name(json_part, "payload_json");
        curl_mimepart* file_part = curl_mime_addpart(mime.get());
        curl_mime_data(file_part, attachment->text.data(), attachment->text.size());
        curl_mime_name(file_part, "files[0]");
        curl_mime_filename(file_part, std::string(attachment->name).c_str());
        curl_mime_type(file_part, "text/plain");
        curl_easy_setopt(handle.get(), CURLOPT_MIMEPOST, mime.get());
    } else {
        body = content_json(content);
        curl_slist* raw_headers = curl_slist_append(nullptr, "Content-Type: application/json");
        headers.reset(raw_headers);
        if (!headers) return fail(ErrorCode::limit, "Discord webhook header allocation failed");
        curl_easy_setopt(handle.get(), CURLOPT_HTTPHEADER, headers.get());
        curl_easy_setopt(handle.get(), CURLOPT_POST, 1L);
        curl_easy_setopt(handle.get(), CURLOPT_POSTFIELDS, body.data());
        curl_easy_setopt(handle.get(), CURLOPT_POSTFIELDSIZE, static_cast<long>(body.size()));
    }
    if (const auto code = curl_easy_perform(handle.get()); code != CURLE_OK) {
        std::string reason = error_text[0] ? std::string(error_text) : std::string(curl_easy_strerror(code));
        if (reason.size() > 160) reason.resize(160);
        return fail(ErrorCode::io, "Discord webhook request failed (" + std::to_string(static_cast<int>(code)) + "): " + reason);
    }
    long status = 0;
    curl_easy_getinfo(handle.get(), CURLINFO_RESPONSE_CODE, &status);
    if (status < 200 || status >= 300) return fail(ErrorCode::io, "Discord webhook rejected the report (HTTP " + std::to_string(status) + ")");
    return {};
}
}

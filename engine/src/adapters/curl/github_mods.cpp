// SPDX-License-Identifier: MIT
// Copyright (c) 2026 OpenLF2 contributors

// Downloads and installs signed content packs listed in the Polish Fighters GitHub catalogue.
// Trust chain: Ed25519 catalogue signature -> envelope size and SHA-256 -> manifest signature
// -> package.zip SHA-256. Nothing from the archive is executed while installing it.
#if defined(_WIN32) && !defined(NOMINMAX)
#define NOMINMAX // curl.h pulls in windows.h; keep std::min/std::max usable.
#endif
#include "openlf2/ports/github_mods.hpp"
#include "openlf2/core/json.hpp"
#include <algorithm>
#include <array>
#include <cctype>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <memory>
#include <mutex>
#include <optional>
#include <random>
#include <set>
#include <vector>
#include <curl/curl.h>
#include <openssl/evp.h>
#include <zlib.h>

namespace openlf2 {
namespace {
namespace fs = std::filesystem;
constexpr std::array<unsigned char, 32> trusted_key{
    0xe6, 0x9b, 0xda, 0x39, 0xfd, 0xd4, 0x26, 0x70, 0xe5, 0x02, 0xab, 0xd7, 0xcc, 0x68, 0xa9, 0x9f,
    0x94, 0x07, 0xe7, 0x9f, 0x40, 0xf6, 0x95, 0x0d, 0x16, 0xb7, 0xa5, 0x30, 0x7b, 0x6f, 0xd4, 0xfc};
constexpr std::string_view catalogue_url = "https://raw.githubusercontent.com/w4sy1/polish-fighters/main/mods/catalog.json";
constexpr std::string_view signature_url = "https://raw.githubusercontent.com/w4sy1/polish-fighters/main/mods/catalog.sig";
constexpr std::string_view asset_prefix = "https://github.com/w4sy1/polish-fighters/releases/download/mods/";
constexpr std::uint64_t envelope_limit = 2047ull * 1024 * 1024;
constexpr std::uint64_t unpacked_limit = 4ull * 1024 * 1024 * 1024;
constexpr std::uint64_t reserve = 64ull * 1024 * 1024;
constexpr std::size_t file_limit = 20000;

std::mutex directory_lock;
fs::path content_directory_value;

struct Session {
    CURLcode status = curl_global_init(CURL_GLOBAL_DEFAULT);
    ~Session() { if (status == CURLE_OK) curl_global_cleanup(); }
};
const Session& session() { static const Session value; return value; }

bool allowed_host(std::string_view url) {
    for (const auto host : {"https://github.com/", "https://raw.githubusercontent.com/",
                            "https://objects.githubusercontent.com/", "https://release-assets.githubusercontent.com/"})
        if (url.starts_with(host)) return true;
    return false;
}

struct Sink {
    std::string* memory = nullptr;
    std::ofstream* file = nullptr;
    EVP_MD_CTX* digest = nullptr;
    std::uint64_t limit = 0;
    std::uint64_t received = 0;
    ModInstallProgress* progress = nullptr;
    bool failed = false;
};
std::size_t receive(char* data, std::size_t size, std::size_t count, void* opaque) noexcept {
    auto& sink = *static_cast<Sink*>(opaque);
    const auto length = size * count;
    if (length > sink.limit - std::min(sink.limit, sink.received)) { sink.failed = true; return 0; }
    try {
        if (sink.memory) sink.memory->append(data, length);
        if (sink.file && !sink.file->write(data, static_cast<std::streamsize>(length))) { sink.failed = true; return 0; }
        if (sink.digest && EVP_DigestUpdate(sink.digest, data, length) != 1) { sink.failed = true; return 0; }
    } catch (...) { sink.failed = true; return 0; }
    sink.received += length;
    if (sink.progress) sink.progress->received = sink.received;
    return length;
}

Result<void> transfer(std::string_view address, Sink& sink, long timeout) {
    if (session().status != CURLE_OK) return fail(ErrorCode::dependency, "HTTP unavailable");
    if (!allowed_host(address)) return fail(ErrorCode::format, "Download outside GitHub");
    std::unique_ptr<CURL, decltype(&curl_easy_cleanup)> handle(curl_easy_init(), curl_easy_cleanup);
    if (!handle) return fail(ErrorCode::dependency, "HTTP unavailable");
    const std::string url(address);
    curl_easy_setopt(handle.get(), CURLOPT_URL, url.c_str());
    curl_easy_setopt(handle.get(), CURLOPT_USERAGENT, "PolishFighters-Mods/1");
    curl_easy_setopt(handle.get(), CURLOPT_FOLLOWLOCATION, 1L);
    curl_easy_setopt(handle.get(), CURLOPT_MAXREDIRS, 5L);
#if LIBCURL_VERSION_NUM >= 0x075500
    curl_easy_setopt(handle.get(), CURLOPT_PROTOCOLS_STR, "https");
    curl_easy_setopt(handle.get(), CURLOPT_REDIR_PROTOCOLS_STR, "https");
#endif
    curl_easy_setopt(handle.get(), CURLOPT_CONNECTTIMEOUT, 15L);
    curl_easy_setopt(handle.get(), CURLOPT_LOW_SPEED_LIMIT, 1L);
    curl_easy_setopt(handle.get(), CURLOPT_LOW_SPEED_TIME, timeout);
    curl_easy_setopt(handle.get(), CURLOPT_NOSIGNAL, 1L);
    curl_easy_setopt(handle.get(), CURLOPT_WRITEFUNCTION, receive);
    curl_easy_setopt(handle.get(), CURLOPT_WRITEDATA, &sink);
#if (defined(_WIN32) || defined(__APPLE__)) && defined(CURLSSLOPT_NATIVE_CA)
    curl_easy_setopt(handle.get(), CURLOPT_SSL_OPTIONS, static_cast<long>(CURLSSLOPT_NATIVE_CA));
#endif
    const auto code = curl_easy_perform(handle.get());
    char* effective = nullptr;
    curl_easy_getinfo(handle.get(), CURLINFO_EFFECTIVE_URL, &effective);
    if (!effective || !allowed_host(effective)) return fail(ErrorCode::format, "Download left the GitHub hosts");
    if (sink.failed) return fail(ErrorCode::limit, "Download exceeds the expected size or cannot be written");
    if (code != CURLE_OK) return fail(ErrorCode::io, std::string("Download failed: ") + curl_easy_strerror(code));
    long status = 0;
    curl_easy_getinfo(handle.get(), CURLINFO_RESPONSE_CODE, &status);
    if (status != 200) return fail(ErrorCode::io, "GitHub answered HTTP " + std::to_string(status));
    return {};
}

bool verify_signature(std::string_view message, std::string_view signature) {
    if (signature.size() != 64) return false;
    std::unique_ptr<EVP_PKEY, decltype(&EVP_PKEY_free)> key(
        EVP_PKEY_new_raw_public_key(EVP_PKEY_ED25519, nullptr, trusted_key.data(), trusted_key.size()), EVP_PKEY_free);
    std::unique_ptr<EVP_MD_CTX, decltype(&EVP_MD_CTX_free)> context(EVP_MD_CTX_new(), EVP_MD_CTX_free);
    if (!key || !context || EVP_DigestVerifyInit(context.get(), nullptr, nullptr, nullptr, key.get()) != 1) return false;
    return EVP_DigestVerify(context.get(), reinterpret_cast<const unsigned char*>(signature.data()), signature.size(),
                            reinterpret_cast<const unsigned char*>(message.data()), message.size()) == 1;
}

std::string hex(const unsigned char* data, unsigned size) {
    constexpr std::string_view digits = "0123456789abcdef";
    std::string text;
    for (unsigned i = 0; i < size; ++i) { text += digits[data[i] >> 4]; text += digits[data[i] & 15]; }
    return text;
}
std::string sha256_text(std::string_view data) {
    std::array<unsigned char, 32> digest{};
    unsigned size = 0;
    EVP_Digest(data.data(), data.size(), digest.data(), &size, EVP_sha256(), nullptr);
    return hex(digest.data(), size);
}

// --- small JSON accessors over ScriptValue ---
const ScriptValue* field(const ScriptValue& value, std::string_view name) {
    const auto* table = std::get_if<ScriptTable>(&value.value);
    if (!table) return nullptr;
    for (const auto& item : *table)
        if (const auto* key = std::get_if<std::string>(&item.key); key && *key == name) return &item.value;
    return nullptr;
}
std::optional<std::string> text(const ScriptValue& value, std::string_view name) {
    const auto* found = field(value, name);
    if (!found) return std::nullopt;
    if (const auto* string = std::get_if<std::string>(&found->value)) return *string;
    return std::nullopt;
}
std::optional<std::uint64_t> number(const ScriptValue& value, std::string_view name) {
    const auto* found = field(value, name);
    if (!found) return std::nullopt;
    if (const auto* integer = std::get_if<std::int32_t>(&found->value); integer && *integer >= 0)
        return static_cast<std::uint64_t>(*integer);
    if (const auto* real = std::get_if<double>(&found->value); real && *real >= 0 && *real < 9.0e15 &&
        *real == static_cast<double>(static_cast<std::uint64_t>(*real)))
        return static_cast<std::uint64_t>(*real);
    return std::nullopt;
}
bool valid_id(std::string_view id) {
    if (id.empty() || id.size() > 64 || id.starts_with("mod-") || id.front() == '-' || id.back() == '-') return false;
    char previous = 0;
    for (const char c : id) {
        if (!((c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c == '-') || (c == '-' && previous == '-')) return false;
        previous = c;
    }
    return true;
}
bool valid_hash(std::string_view value) {
    return value.size() == 64 && std::all_of(value.begin(), value.end(), [](char c) {
        return (c >= '0' && c <= '9') || (c >= 'a' && c <= 'f'); });
}

// --- minimal ZIP reader (stored + deflate, ZIP64 aware) over a byte range of a file ---
struct ZipItem {
    std::string name;
    std::uint16_t method = 0, flags = 0;
    std::uint32_t crc = 0;
    std::uint64_t compressed = 0, size = 0, local = 0;
};
std::uint16_t u16(const unsigned char* p) { return static_cast<std::uint16_t>(p[0] | (p[1] << 8)); }
std::uint32_t u32(const unsigned char* p) { return u16(p) | (static_cast<std::uint32_t>(u16(p + 2)) << 16); }
std::uint64_t u64(const unsigned char* p) { return u32(p) | (static_cast<std::uint64_t>(u32(p + 4)) << 32); }

bool read_at(std::ifstream& file, std::uint64_t offset, unsigned char* target, std::size_t size) {
    file.clear();
    file.seekg(static_cast<std::streamoff>(offset));
    return static_cast<bool>(file.read(reinterpret_cast<char*>(target), static_cast<std::streamsize>(size)));
}

Result<std::vector<ZipItem>> zip_entries(std::ifstream& file, std::uint64_t base, std::uint64_t length) {
    const auto tail_size = static_cast<std::size_t>(std::min<std::uint64_t>(length, 65557));
    if (tail_size < 22) return fail(ErrorCode::format, "ZIP is too small");
    std::vector<unsigned char> tail(tail_size);
    if (!read_at(file, base + length - tail_size, tail.data(), tail_size)) return fail(ErrorCode::io, "Cannot read ZIP");
    std::size_t end = tail_size - 22 + 1;
    bool found = false;
    while (end-- > 0) if (u32(&tail[end]) == 0x06054b50) { found = true; break; }
    if (!found) return fail(ErrorCode::format, "ZIP end record missing");
    std::uint64_t count = u16(&tail[end + 10]), directory_size = u32(&tail[end + 12]), directory = u32(&tail[end + 16]);
    if ((count == 0xffff || directory_size == 0xffffffff || directory == 0xffffffff) && end >= 20 &&
        u32(&tail[end - 20]) == 0x07064b50) {
        const auto record = u64(&tail[end - 12]);
        std::array<unsigned char, 56> zip64{};
        if (record + 56 > length || !read_at(file, base + record, zip64.data(), zip64.size()) || u32(zip64.data()) != 0x06064b50)
            return fail(ErrorCode::format, "ZIP64 record invalid");
        count = u64(&zip64[32]); directory_size = u64(&zip64[40]); directory = u64(&zip64[48]);
    }
    if (count > file_limit + 8 || directory + directory_size > length || directory_size > 64ull * 1024 * 1024)
        return fail(ErrorCode::format, "ZIP directory invalid");
    std::vector<unsigned char> data(static_cast<std::size_t>(directory_size));
    if (!read_at(file, base + directory, data.data(), data.size())) return fail(ErrorCode::io, "Cannot read ZIP directory");
    std::vector<ZipItem> items;
    std::size_t at = 0;
    for (std::uint64_t i = 0; i < count; ++i) {
        if (at + 46 > data.size() || u32(&data[at]) != 0x02014b50) return fail(ErrorCode::format, "ZIP entry invalid");
        ZipItem item;
        item.flags = u16(&data[at + 8]); item.method = u16(&data[at + 10]); item.crc = u32(&data[at + 16]);
        item.compressed = u32(&data[at + 20]); item.size = u32(&data[at + 24]);
        const std::size_t name = u16(&data[at + 28]), extra = u16(&data[at + 30]), comment = u16(&data[at + 32]);
        item.local = u32(&data[at + 42]);
        if (at + 46 + name + extra + comment > data.size()) return fail(ErrorCode::format, "ZIP entry truncated");
        item.name.assign(reinterpret_cast<const char*>(&data[at + 46]), name);
        std::size_t cursor = at + 46 + name;
        const std::size_t extra_end = cursor + extra;
        while (cursor + 4 <= extra_end) {
            const auto tag = u16(&data[cursor]), size = u16(&data[cursor + 2]);
            if (cursor + 4 + size > extra_end) break;
            if (tag == 1) {
                std::size_t value = cursor + 4;
                const auto take = [&](std::uint64_t& target) {
                    if (target == 0xffffffff && value + 8 <= cursor + 4 + size) { target = u64(&data[value]); value += 8; }
                };
                take(item.size); take(item.compressed); take(item.local);
            }
            cursor += 4 + size;
        }
        at = extra_end + comment;
        items.push_back(std::move(item));
    }
    return items;
}

Result<std::uint64_t> data_offset(std::ifstream& file, std::uint64_t base, std::uint64_t length, const ZipItem& item) {
    std::array<unsigned char, 30> header{};
    if (item.local + 30 > length || !read_at(file, base + item.local, header.data(), header.size()) ||
        u32(header.data()) != 0x04034b50) return fail(ErrorCode::format, "ZIP local header invalid");
    const auto start = item.local + 30 + u16(&header[26]) + u16(&header[28]);
    if (start + item.compressed > length) return fail(ErrorCode::format, "ZIP data outside archive");
    return base + start;
}

// Streams one entry to `output` (or only hashes it when `output` is null); checks size and CRC.
Result<void> extract(std::ifstream& file, std::uint64_t offset, const ZipItem& item, std::ofstream* output,
                     EVP_MD_CTX* digest) {
    if (item.flags & 1) return fail(ErrorCode::unsupported, "Encrypted ZIP entries are unsupported");
    if (item.method != 0 && item.method != 8) return fail(ErrorCode::unsupported, "Unsupported ZIP compression");
    file.clear();
    file.seekg(static_cast<std::streamoff>(offset));
    std::vector<char> input(1 << 16), produced(1 << 17);
    std::uint64_t remaining = item.compressed, written = 0;
    uLong crc = crc32(0L, Z_NULL, 0);
    const auto emit = [&](const char* data, std::size_t size) -> bool {
        written += size;
        if (written > item.size) return false;
        crc = crc32(crc, reinterpret_cast<const Bytef*>(data), static_cast<uInt>(size));
        if (digest && EVP_DigestUpdate(digest, data, size) != 1) return false;
        return !output || static_cast<bool>(output->write(data, static_cast<std::streamsize>(size)));
    };
    z_stream stream{};
    const bool deflated = item.method == 8;
    if (deflated && inflateInit2(&stream, -MAX_WBITS) != Z_OK) return fail(ErrorCode::dependency, "zlib unavailable");
    std::unique_ptr<z_stream, void (*)(z_stream*)> guard(deflated ? &stream : nullptr, [](z_stream* s) { inflateEnd(s); });
    int status = Z_OK;
    while (remaining > 0) {
        const auto chunk = static_cast<std::size_t>(std::min<std::uint64_t>(remaining, input.size()));
        if (!file.read(input.data(), static_cast<std::streamsize>(chunk))) return fail(ErrorCode::io, "Cannot read ZIP data");
        remaining -= chunk;
        if (!deflated) { if (!emit(input.data(), chunk)) return fail(ErrorCode::limit, "ZIP entry exceeds declared size"); continue; }
        stream.next_in = reinterpret_cast<Bytef*>(input.data());
        stream.avail_in = static_cast<uInt>(chunk);
        while (stream.avail_in > 0 && status != Z_STREAM_END) {
            stream.next_out = reinterpret_cast<Bytef*>(produced.data());
            stream.avail_out = static_cast<uInt>(produced.size());
            status = inflate(&stream, Z_NO_FLUSH);
            if (status != Z_OK && status != Z_STREAM_END) return fail(ErrorCode::format, "Corrupt ZIP data");
            if (!emit(produced.data(), produced.size() - stream.avail_out)) return fail(ErrorCode::limit, "ZIP entry exceeds declared size");
        }
    }
    if (deflated) {
        while (status != Z_STREAM_END) {
            stream.next_out = reinterpret_cast<Bytef*>(produced.data());
            stream.avail_out = static_cast<uInt>(produced.size());
            status = inflate(&stream, Z_FINISH);
            if (status != Z_OK && status != Z_STREAM_END && status != Z_BUF_ERROR) return fail(ErrorCode::format, "Corrupt ZIP data");
            const auto size = produced.size() - stream.avail_out;
            if (size == 0 && status != Z_STREAM_END) return fail(ErrorCode::format, "Truncated ZIP data");
            if (!emit(produced.data(), size)) return fail(ErrorCode::limit, "ZIP entry exceeds declared size");
        }
    }
    if (written != item.size || crc != item.crc) return fail(ErrorCode::format, "ZIP entry checksum mismatch: " + item.name);
    return {};
}

Result<std::string> read_small(std::ifstream& file, std::uint64_t base, std::uint64_t length, const ZipItem& item,
                               std::size_t limit) {
    if (item.size > limit || item.method != 0) return fail(ErrorCode::format, "Signed metadata invalid");
    auto offset = data_offset(file, base, length, item);
    if (!offset) return std::unexpected(offset.error());
    std::string value(static_cast<std::size_t>(item.size), '\0');
    if (!read_at(file, *offset, reinterpret_cast<unsigned char*>(value.data()), value.size()))
        return fail(ErrorCode::io, "Cannot read signed metadata");
    return value;
}

bool safe_name(std::string_view name) {
    if (name.empty() || name.size() > 240 || name.front() == '/' || name.find('\\') != std::string_view::npos ||
        name.find(':') != std::string_view::npos) return false;
    std::size_t start = 0;
    while (start <= name.size()) {
        const auto end = std::min(name.find('/', start), name.size());
        const auto part = name.substr(start, end - start);
        if (part.empty() || part == "." || part == ".." || part.back() == ' ' || part.back() == '.') return false;
        for (const char c : part) if (static_cast<unsigned char>(c) < 32 || std::strchr("<>\"|?*", c)) return false;
        start = end + 1;
    }
    std::string lower(name);
    std::transform(lower.begin(), lower.end(), lower.begin(), [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
    for (const auto suffix : {".exe", ".dll", ".so", ".dylib", ".bat", ".cmd", ".ps1", ".sh", ".py", ".com", ".scr", ".msi",
                              ".jar", ".vbs", ".js", ".apk", ".dex"})
        if (lower.ends_with(suffix)) return false;
    return true;
}

std::string lowercase(std::string value) {
    std::transform(value.begin(), value.end(), value.begin(), [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
    return value;
}

Result<std::string> install_envelope(const fs::path& envelope, const fs::path& packs, std::string_view id,
                                     ModInstallProgress& progress) {
    std::ifstream file(envelope, std::ios::binary);
    if (!file) return fail(ErrorCode::io, "Cannot open the downloaded package");
    const auto length = fs::file_size(envelope);
    auto entries = zip_entries(file, 0, length);
    if (!entries) return std::unexpected(entries.error());
    const std::array<std::string_view, 5> order{"catalog.json", "catalog.sig", "manifest.json", "manifest.sig", "package.zip"};
    if (entries->size() != order.size()) return fail(ErrorCode::format, "Invalid signed envelope");
    for (std::size_t i = 0; i < order.size(); ++i)
        if ((*entries)[i].name != order[i] || (*entries)[i].method != 0) return fail(ErrorCode::format, "Invalid signed envelope");
    auto index = read_small(file, 0, length, (*entries)[0], 1024 * 1024);
    auto index_signature = read_small(file, 0, length, (*entries)[1], 64);
    auto manifest_text = read_small(file, 0, length, (*entries)[2], 1024 * 1024);
    auto manifest_signature = read_small(file, 0, length, (*entries)[3], 64);
    if (!index || !index_signature || !manifest_text || !manifest_signature) return fail(ErrorCode::format, "Invalid signed envelope");
    if (!verify_signature(*index, *index_signature) || !verify_signature(*manifest_text, *manifest_signature))
        return fail(ErrorCode::format, "Invalid package signature");
    auto catalogue = parse_json(*index);
    auto manifest = parse_json(*manifest_text);
    if (!catalogue || !manifest) return fail(ErrorCode::format, "Invalid signed metadata");
    const auto version = text(*manifest, "version");
    const auto type = text(*manifest, "package_type");
    const auto size = number(*manifest, "size_bytes");
    const auto unpacked = number(*manifest, "unpacked_size_bytes");
    const auto sha = text(*manifest, "sha256");
    const auto* installation = field(*manifest, "installation");
    const auto* pins = field(*catalogue, "manifests");
    if (text(*manifest, "id") != std::string(id) || !version || type != std::string("content-pack") || !size || !unpacked ||
        !sha || !installation || text(*installation, "method") != std::string("content-pack-zip") || !pins ||
        text(*catalogue, "channel") != std::string("stable") ||
        text(*pins, std::string(id) + "@" + *version) != sha256_text(*manifest_text))
        return fail(ErrorCode::format, "Signed manifest does not describe this content pack");
    const auto& payload = (*entries)[4];
    if (payload.size != *size || *unpacked > unpacked_limit) return fail(ErrorCode::format, "Package size differs from manifest");
    auto payload_offset = data_offset(file, 0, length, payload);
    if (!payload_offset) return std::unexpected(payload_offset.error());
    // Hash package.zip in place: it is stored, so its bytes are a range of the envelope.
    progress.phase = 2;
    {
        std::unique_ptr<EVP_MD_CTX, decltype(&EVP_MD_CTX_free)> digest(EVP_MD_CTX_new(), EVP_MD_CTX_free);
        if (!digest || EVP_DigestInit_ex(digest.get(), EVP_sha256(), nullptr) != 1) return fail(ErrorCode::dependency, "SHA-256 unavailable");
        auto checked = extract(file, *payload_offset, payload, nullptr, digest.get());
        if (!checked) return std::unexpected(checked.error());
        std::array<unsigned char, 32> value{};
        unsigned produced = 0;
        EVP_DigestFinal_ex(digest.get(), value.data(), &produced);
        if (hex(value.data(), produced) != *sha) return fail(ErrorCode::format, "Package SHA-256 differs from manifest");
    }
    auto items = zip_entries(file, *payload_offset, payload.size);
    if (!items) return std::unexpected(items.error());
    std::uint64_t total = 0;
    std::set<std::string> names;
    std::vector<const ZipItem*> files;
    for (const auto& item : *items) {
        if (item.name.ends_with('/')) continue;
        if (!safe_name(item.name) || !names.insert(lowercase(item.name)).second || files.size() >= file_limit)
            return fail(ErrorCode::format, "Unsafe file in content pack: " + item.name);
        total += item.size;
        if (total > *unpacked) return fail(ErrorCode::format, "Unpacked size differs from manifest");
        files.push_back(&item);
    }
    if (total != *unpacked || !names.contains("package.manifest")) return fail(ErrorCode::format, "Content pack is incomplete");
    std::error_code error;
    const auto space = fs::space(packs, error);
    if (!error && space.available < total + reserve) return fail(ErrorCode::limit, "Not enough free disk space");
    std::mt19937_64 random(std::random_device{}());
    const auto staging = packs / (".staging-" + std::string(id) + "-" + std::to_string(random() & 0xffffffff));
    const auto cleanup = [&](const fs::path& path) { std::error_code ignored; fs::remove_all(path, ignored); };
    progress.phase = 3;
    for (const auto* item : files) {
        const auto target = staging / fs::path(std::u8string(item->name.begin(), item->name.end()));
        fs::create_directories(target.parent_path(), error);
        if (error) { cleanup(staging); return fail(ErrorCode::io, "Cannot create content-pack folder"); }
        auto offset = data_offset(file, *payload_offset, payload.size, *item);
        if (!offset) { cleanup(staging); return std::unexpected(offset.error()); }
        std::ofstream output(target, std::ios::binary | std::ios::trunc);
        if (!output) { cleanup(staging); return fail(ErrorCode::io, "Cannot write content-pack file"); }
        auto copied = extract(file, *offset, *item, &output, nullptr);
        output.close();
        if (!copied || !output) { cleanup(staging); return copied ? fail(ErrorCode::io, "Cannot write content-pack file") : std::unexpected(copied.error()); }
        ++progress.files;
    }
    {
        std::ifstream manifest_file(staging / "package.manifest", std::ios::binary);
        std::string line;
        bool declared = false;
        while (std::getline(manifest_file, line)) {
            if (!line.empty() && line.back() == '\r') line.pop_back();
            declared = declared || line == "id=" + std::string(id);
        }
        if (!declared) { cleanup(staging); return fail(ErrorCode::format, "package.manifest declares a different ID"); }
    }
    const auto target = packs / std::string(id);
    const auto previous = packs / (".previous-" + std::string(id) + "-" + std::to_string(random() & 0xffffffff));
    const bool replace = fs::exists(target, error);
    if (replace) {
        fs::rename(target, previous, error);
        if (error) { cleanup(staging); return fail(ErrorCode::io, "Close the game data of this mod and try again"); }
    }
    fs::rename(staging, target, error);
    if (error) {
        if (replace) { std::error_code ignored; fs::rename(previous, target, ignored); }
        cleanup(staging);
        return fail(ErrorCode::io, "Cannot publish the installed mod");
    }
    if (replace) cleanup(previous);
    return std::string(id);
}
}

void set_mod_content_directory(const fs::path& directory) {
    std::scoped_lock lock(directory_lock);
    content_directory_value = directory;
}
fs::path mod_content_directory() {
    std::scoped_lock lock(directory_lock);
    return content_directory_value;
}
bool github_mods_supported() noexcept { return true; }

Result<std::string> github_mod_catalogue() {
    std::string raw, signature;
    Sink catalogue_sink{&raw, nullptr, nullptr, 1024 * 1024};
    auto fetched = transfer(catalogue_url, catalogue_sink, 30);
    if (!fetched) return std::unexpected(fetched.error());
    Sink signature_sink{&signature, nullptr, nullptr, 64};
    fetched = transfer(signature_url, signature_sink, 30);
    if (!fetched) return std::unexpected(fetched.error());
    if (!verify_signature(raw, signature)) return fail(ErrorCode::format, "Mod catalogue signature is invalid");
    auto document = parse_json(raw);
    if (!document || text(*document, "format") != std::string("polish-fighters-mods") ||
        text(*document, "channel") != std::string("stable")) return fail(ErrorCode::format, "Unsupported mod catalogue");
    return raw;
}

Result<std::string> github_mod_install(std::string_view verified_catalogue, std::string_view id, ModInstallProgress& progress) {
    progress.received = 0; progress.total = 0; progress.files = 0; progress.phase = 1;
    if (!valid_id(id)) return fail(ErrorCode::format, "Invalid mod ID");
    auto document = parse_json(verified_catalogue);
    if (!document) return fail(ErrorCode::format, "Invalid mod catalogue");
    const auto* packages = field(*document, "packages");
    const auto* list = packages ? std::get_if<ScriptTable>(&packages->value) : nullptr;
    const ScriptValue* entry = nullptr;
    if (list) for (const auto& item : *list) if (text(item.value, "id") == std::string(id)) { entry = &item.value; break; }
    if (!entry) return fail(ErrorCode::format, "Mod is not in the catalogue");
    const auto url = text(*entry, "url");
    const auto version = text(*entry, "version");
    const auto size = number(*entry, "size_bytes");
    const auto sha = text(*entry, "sha256");
    if (!url || !version || !size || !sha || !valid_hash(*sha) || *size == 0 || *size > envelope_limit ||
        !url->starts_with(asset_prefix) || *url != std::string(asset_prefix) + std::string(id) + "-" + *version + ".zip")
        return fail(ErrorCode::format, "Invalid catalogue entry");
    const auto packs = mod_content_directory();
    if (packs.empty()) return fail(ErrorCode::platform, "Content-pack folder is unknown");
    std::error_code error;
    fs::create_directories(packs, error);
    const auto envelope = packs / (".download-" + std::string(id) + ".zip");
    progress.total = *size;
    {
        std::ofstream output(envelope, std::ios::binary | std::ios::trunc);
        if (!output) return fail(ErrorCode::io, "Cannot write into the content-pack folder");
        std::unique_ptr<EVP_MD_CTX, decltype(&EVP_MD_CTX_free)> digest(EVP_MD_CTX_new(), EVP_MD_CTX_free);
        if (!digest || EVP_DigestInit_ex(digest.get(), EVP_sha256(), nullptr) != 1) return fail(ErrorCode::dependency, "SHA-256 unavailable");
        Sink sink{nullptr, &output, digest.get(), *size, 0, &progress};
        auto fetched = transfer(*url, sink, 60);
        output.close();
        std::array<unsigned char, 32> value{};
        unsigned produced = 0;
        EVP_DigestFinal_ex(digest.get(), value.data(), &produced);
        if (!fetched || sink.received != *size || hex(value.data(), produced) != *sha) {
            fs::remove(envelope, error);
            return fetched ? fail(ErrorCode::format, "Downloaded file does not match the signed catalogue")
                           : std::unexpected(fetched.error());
        }
    }
    auto installed = install_envelope(envelope, packs, id, progress);
    fs::remove(envelope, error);
    progress.phase = 0;
    return installed;
}
}

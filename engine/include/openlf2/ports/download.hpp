// SPDX-License-Identifier: MIT
// Copyright (c) 2026 OpenLF2 contributors

#pragma once
#include "openlf2/core/result.hpp"
#include <cstdint>
#include <functional>
#include <memory>
#include <string_view>
#include <string>

namespace openlf2 {
// Bytes received so far and the size the server announced (0 while unknown). It is called on
// the thread running fetch(); returning false cancels the transfer.
using DownloadProgress = std::function<bool(std::uint64_t received, std::uint64_t total)>;
class Downloader {
public:
    virtual ~Downloader() = default;
    // Downloads an HTTPS `url` into memory, following HTTPS redirects. Transfers larger than
    // `limit` bytes fail. Independent calls may run on worker threads.
    virtual Result<Bytes> fetch(std::string_view url, std::size_t limit,
                                const DownloadProgress& progress) const = 0;
};
// Call it on the main thread. Fails with ErrorCode::dependency when the build has no
// download support.
Result<std::unique_ptr<Downloader>> make_downloader();
// Bounded account API call. HTTPS remotely; plain HTTP is limited to loopback.
Result<std::string> account_post(std::string_view base, std::string_view operation,
                                 std::string_view body, std::string_view bearer);
// Public, bounded release metadata from this game's GitHub repository. No account token.
Result<std::string> github_releases();
}

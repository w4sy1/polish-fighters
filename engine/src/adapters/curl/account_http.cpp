#include "openlf2/ports/download.hpp"
#include "letsencrypt_roots.hpp"
#include <curl/curl.h>
#include <memory>
#include <string>

namespace openlf2 {
namespace {
struct Session {
    CURLcode status=curl_global_init(CURL_GLOBAL_DEFAULT);
    ~Session(){ if(status==CURLE_OK)curl_global_cleanup(); }
};
std::size_t receive(char* data,std::size_t size,std::size_t count,void* opaque) noexcept {
    auto& result=*static_cast<std::string*>(opaque);
    if(size!=1 || count>65536-result.size())return 0;
    try { result.append(data,count);return count; } catch(...) {return 0;}
}
std::size_t receive_releases(char* data,std::size_t size,std::size_t count,void* opaque) noexcept {
    auto& result=*static_cast<std::string*>(opaque);
    constexpr std::size_t limit=512*1024;
    if(size!=1 || count>limit-result.size())return 0;
    try {result.append(data,count);return count;}catch(...){return 0;}
}
}
Result<std::string> account_post(std::string_view base,std::string_view operation,
                                 std::string_view body,std::string_view bearer) {
    static const Session session;
    if(session.status!=CURLE_OK)return fail(ErrorCode::dependency,"Account HTTP unavailable");
    if(base.size()>512 || body.size()>8192 || bearer.size()>128 ||
       bearer.find_first_of("\r\n")!=std::string_view::npos)
        return fail(ErrorCode::limit,"Account request exceeds limit");
    if(operation!="login" && operation!="register" && operation!="logout" &&
       operation!="list-rooms" && operation!="publish-room" && operation!="delete-room" && operation!="heartbeat-room" &&
       operation!="relay-ticket" && operation!="bug-report")
        return fail(ErrorCode::format,"Unknown account operation");
    const auto address=std::string(base);
    std::unique_ptr<CURLU,decltype(&curl_url_cleanup)> url(curl_url(),curl_url_cleanup);
    if(!url || curl_url_set(url.get(),CURLUPART_URL,address.c_str(),0)!=CURLUE_OK)
        return fail(ErrorCode::format,"Invalid account server URL");
    const auto part=[&](CURLUPart component){
        char* text=nullptr;std::string result;
        if(curl_url_get(url.get(),component,&text,0)==CURLUE_OK){result=text;curl_free(text);}return result;
    };
    const auto scheme=part(CURLUPART_SCHEME),host=part(CURLUPART_HOST);
    const bool local=host=="127.0.0.1" || host=="localhost" || host=="[::1]";
    if((scheme!="https" && !(scheme=="http" && local)) ||
       !part(CURLUPART_USER).empty() || !part(CURLUPART_PASSWORD).empty() ||
       address.find_first_of("?#")!=std::string::npos)
        return fail(ErrorCode::format,"Use an HTTPS server URL without credentials, query or fragment; HTTP is allowed only on localhost");
    std::string endpoint=part(CURLUPART_URL);
    while(endpoint.ends_with('/'))endpoint.pop_back();
    endpoint+="/v1/";endpoint+=operation;
    std::unique_ptr<CURL,decltype(&curl_easy_cleanup)> handle(curl_easy_init(),curl_easy_cleanup);
    if(!handle)return fail(ErrorCode::dependency,"Account HTTP unavailable");
    curl_slist* raw_headers=curl_slist_append(nullptr,"Content-Type: application/json");
    // Shared hosting may answer HTML clients with a browser verification page; ask for JSON.
    if(raw_headers){auto* accepted=curl_slist_append(raw_headers,"Accept: application/json");if(accepted)raw_headers=accepted;}
    const auto authorization="Authorization: Bearer "+std::string(bearer);
    if(!bearer.empty()){
        auto* appended=curl_slist_append(raw_headers,authorization.c_str());
        if(!appended){curl_slist_free_all(raw_headers);return fail(ErrorCode::limit,"Account header allocation failed");}
        raw_headers=appended;
    }
    std::unique_ptr<curl_slist,decltype(&curl_slist_free_all)> headers(raw_headers,curl_slist_free_all);
    if(!headers)return fail(ErrorCode::limit,"Account header allocation failed");
    std::string response;
#ifdef __ANDROID__
    // Without the system bundle OpenSSL finds no trusted CA on Android and every HTTPS
    // account request fails. Read it once; later requests reuse the copy.
    static const Result<std::string> ca_bundle=android_system_ca_bundle();
    if(!ca_bundle)return fail(ErrorCode::dependency,"Android CA certificates unavailable");
    curl_blob certificates{const_cast<char*>(ca_bundle->data()),ca_bundle->size(),CURL_BLOB_NOCOPY};
    curl_easy_setopt(handle.get(),CURLOPT_CAINFO_BLOB,&certificates);
#elif defined(_WIN32)
    // The Windows store is used as well (CURLSSLOPT_NATIVE_CA below); these roots cover PCs
    // whose store was never filled with ISRG Root X1, the root of the project's server.
    curl_blob certificates{const_cast<char*>(letsencrypt_roots_pem),sizeof(letsencrypt_roots_pem)-1,CURL_BLOB_NOCOPY};
    curl_easy_setopt(handle.get(),CURLOPT_CAINFO_BLOB,&certificates);
#endif
    // Like the update check and the mod downloads; without it OpenSSL on Windows trusts no root
    // at all and every account request failed.
#if (defined(_WIN32) || defined(__APPLE__)) && defined(CURLSSLOPT_NATIVE_CA)
    curl_easy_setopt(handle.get(),CURLOPT_SSL_OPTIONS,static_cast<long>(CURLSSLOPT_NATIVE_CA));
#endif
    char error_text[CURL_ERROR_SIZE]{};
    curl_easy_setopt(handle.get(),CURLOPT_ERRORBUFFER,error_text);
    curl_easy_setopt(handle.get(),CURLOPT_URL,endpoint.c_str());
    curl_easy_setopt(handle.get(),CURLOPT_HTTPHEADER,headers.get());
    curl_easy_setopt(handle.get(),CURLOPT_POST,1L);
    curl_easy_setopt(handle.get(),CURLOPT_POSTFIELDS,body.data());
    curl_easy_setopt(handle.get(),CURLOPT_POSTFIELDSIZE,static_cast<long>(body.size()));
    // Shared hosting may start the service on the first request after a quiet period.
    curl_easy_setopt(handle.get(),CURLOPT_CONNECTTIMEOUT,10L);
    curl_easy_setopt(handle.get(),CURLOPT_TIMEOUT,25L);
    curl_easy_setopt(handle.get(),CURLOPT_NOSIGNAL,1L);
    curl_easy_setopt(handle.get(),CURLOPT_FOLLOWLOCATION,0L);
    curl_easy_setopt(handle.get(),CURLOPT_WRITEFUNCTION,receive);
    curl_easy_setopt(handle.get(),CURLOPT_WRITEDATA,&response);
    if(const auto code=curl_easy_perform(handle.get());code!=CURLE_OK){
        // The reason is shown to the player, so a report says whether it was DNS, TLS or a timeout.
        std::string reason=error_text[0]?std::string(error_text):std::string(curl_easy_strerror(code));
        if(reason.size()>160)reason.resize(160);
        return fail(ErrorCode::io,"Account request failed ("+std::to_string(static_cast<int>(code))+"): "+reason);
    }
    long status=0;curl_easy_getinfo(handle.get(),CURLINFO_RESPONSE_CODE,&status);
    if(status<200 || status>=500)return fail(ErrorCode::io,"Account server unavailable");
    return response;
}
Result<std::string> github_releases() {
    static const Session session;
    if(session.status!=CURLE_OK)return fail(ErrorCode::dependency,"Update HTTP unavailable");
    std::unique_ptr<CURL,decltype(&curl_easy_cleanup)> handle(curl_easy_init(),curl_easy_cleanup);
    if(!handle)return fail(ErrorCode::dependency,"Update HTTP unavailable");
    std::string response;
    curl_easy_setopt(handle.get(),CURLOPT_URL,"https://api.github.com/repos/w4sy1/polish-fighters/releases?per_page=5");
    curl_easy_setopt(handle.get(),CURLOPT_USERAGENT,"PolishFighters-UpdateCheck/1");
    curl_easy_setopt(handle.get(),CURLOPT_CONNECTTIMEOUT,3L);
    curl_easy_setopt(handle.get(),CURLOPT_TIMEOUT,5L);
    curl_easy_setopt(handle.get(),CURLOPT_NOSIGNAL,1L);
    curl_easy_setopt(handle.get(),CURLOPT_FOLLOWLOCATION,0L);
    curl_easy_setopt(handle.get(),CURLOPT_WRITEFUNCTION,receive_releases);
    curl_easy_setopt(handle.get(),CURLOPT_WRITEDATA,&response);
#if (defined(_WIN32) || defined(__APPLE__)) && defined(CURLSSLOPT_NATIVE_CA)
    curl_easy_setopt(handle.get(),CURLOPT_SSL_OPTIONS,static_cast<long>(CURLSSLOPT_NATIVE_CA));
#endif
    if(curl_easy_perform(handle.get())!=CURLE_OK)return fail(ErrorCode::io,"GitHub update check unavailable");
    long status=0;curl_easy_getinfo(handle.get(),CURLINFO_RESPONSE_CODE,&status);
    if(status!=200)return fail(ErrorCode::io,"GitHub update check unavailable");
    return response;
}
}

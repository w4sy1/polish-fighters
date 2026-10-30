// SPDX-License-Identifier: MIT
#pragma once
#include "openlf2/engine/room.hpp"
#include <chrono>
#include <memory>
#include <string_view>
namespace openlf2 {
// Multi-client TCP room service. The host player joins through the same client protocol.
// Transport/lobby/lockstep only: the gameplay binding is a separate integration.
class RoomHost {
public:
 static Result<std::unique_ptr<RoomHost>> create(int capacity,std::string profile,std::int32_t seed=42,
    std::chrono::milliseconds timeout=std::chrono::seconds(30));
 ~RoomHost();
 Result<void> listen(std::string_view address,std::uint16_t port);
 Result<void> poll();
 [[nodiscard]] std::uint16_t port() const;
 [[nodiscard]] const Room& room() const;
private:
 struct Impl;
 explicit RoomHost(std::unique_ptr<Impl> impl);
 std::unique_ptr<Impl> impl_;
};
}

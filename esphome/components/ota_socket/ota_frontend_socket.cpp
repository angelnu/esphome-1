#include "ota_frontend_socket.h"

#include "esphome/core/application.h"
#include "esphome/core/log.h"
#include "esphome/core/hal.h"
#include "esphome/core/util.h"

#include "esphome/components/ota/ota_component.h"
#include "esphome/components/md5/md5.h"
#include "esphome/components/network/util.h"

#include <cerrno>
#include <cstdio>

namespace esphome {
namespace ota_socket {

static const char *const TAG = "ota_socket";

OTAFrontendSocket::OTAFrontendSocket() {}

void OTAFrontendSocket::set_port(uint16_t port) { this->port_ = port; }

float OTAFrontendSocket::get_setup_priority() const { return setup_priority::AFTER_WIFI; }

void OTAFrontendSocket::setup() {
  server_ = socket::socket_ip(SOCK_STREAM, 0);
  if (server_ == nullptr) {
    ESP_LOGW(TAG, "Could not create socket.");
    this->mark_failed();
    return;
  }
  int enable = 1;
  int err = server_->setsockopt(SOL_SOCKET, SO_REUSEADDR, &enable, sizeof(int));
  if (err != 0) {
    ESP_LOGW(TAG, "Socket unable to set reuseaddr: errno %d", err);
    // we can still continue
  }
  err = server_->setblocking(false);
  if (err != 0) {
    ESP_LOGW(TAG, "Socket unable to set nonblocking mode: errno %d", err);
    this->mark_failed();
    return;
  }

  struct sockaddr_storage server;

  socklen_t sl = socket::set_sockaddr_any((struct sockaddr *) &server, sizeof(server), this->port_);
  if (sl == 0) {
    ESP_LOGW(TAG, "Socket unable to set sockaddr: errno %d", errno);
    this->mark_failed();
    return;
  }

  err = server_->bind((struct sockaddr *) &server, sizeof(server));
  if (err != 0) {
    ESP_LOGW(TAG, "Socket unable to bind: errno %d", errno);
    this->mark_failed();
    return;
  }

  err = server_->listen(4);
  if (err != 0) {
    ESP_LOGW(TAG, "Socket unable to listen: errno %d", errno);
    this->mark_failed();
    return;
  }

  this->dump_config();
}

void OTAFrontendSocket::dump_config() {
  ESP_LOGCONFIG(TAG, "Over-The-Air Socket Updates:");
  ESP_LOGCONFIG(TAG, "  Address: %s:%u", network::get_use_address().c_str(), this->port_);
}

void OTAFrontendSocket::loop() { this->handle_(); }

void OTAFrontendSocket::handle_() {
  if (client_ == nullptr) {
    struct sockaddr_storage source_addr;
    socklen_t addr_len = sizeof(source_addr);
    client_ = server_->accept((struct sockaddr *) &source_addr, &addr_len);
  }
  if (client_ == nullptr)
    return;

  int enable = 1;
  int err = client_->setsockopt(IPPROTO_TCP, TCP_NODELAY, &enable, sizeof(int));
  if (err != 0) {
    ESP_LOGW(TAG, "Socket could not enable tcp nodelay, errno: %d", errno);
    return;
  }

  ESP_LOGD(TAG, "Starting OTA Update from %s...", this->client_->getpeername().c_str());
  ota::global_ota_component->do_ota_session(this);
}

ssize_t OTAFrontendSocket::read(uint8_t *buf, size_t len) { return this->client_->read(buf, len); }
ssize_t OTAFrontendSocket::write(const uint8_t *buf, size_t len) { return this->client_->write(buf, len); }
void OTAFrontendSocket::close_session() {
  this->client_->close();
  this->client_ = nullptr;
}

}  // namespace ota_socket
}  // namespace esphome

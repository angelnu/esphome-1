import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.const import (
    CONF_ID,
    CONF_PORT,
)

CODEOWNERS = ["@esphome/core"]
DEPENDENCIES = ["network"]
AUTO_LOAD = ["socket", "ota"]

ota_ns = cg.esphome_ns.namespace("ota_socket")
OTAComponent = ota_ns.class_("OTAFrontendSocket", cg.Component)


CONFIG_SCHEMA = cv.All(
    cv.Schema(
        {
            cv.GenerateID(): cv.declare_id(OTAComponent),
            cv.SplitDefault(
                CONF_PORT,
                esp8266=8266,
                esp32=3232,
                rp2040=2040,
                bk72xx=8892,
                rtl87xx=8892,
            ): cv.port,
        }
    ).extend(cv.COMPONENT_SCHEMA)
)


async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    cg.add(var.set_port(config[CONF_PORT]))

    await cg.register_component(var, config)

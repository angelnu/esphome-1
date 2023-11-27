from esphome.cpp_generator import RawExpression
import esphome.codegen as cg
import esphome.config_validation as cv
from esphome import automation
from esphome.const import (
    CONF_ID,
    CONF_NUM_ATTEMPTS,
    CONF_PASSWORD,
    CONF_REBOOT_TIMEOUT,
    CONF_SAFE_MODE,
    CONF_TRIGGER_ID,
    CONF_OTA,
    KEY_PAST_SAFE_MODE,
)
from esphome.core import CORE, coroutine_with_priority

CODEOWNERS = ["@esphome/core"]
AUTO_LOAD = ["md5", "ota_socket"]

CONF_UNPROTECTED_WRITES = "unprotected_writes"
CONF_ON_STATE_CHANGE = "on_state_change"
CONF_ON_BEGIN = "on_begin"
CONF_ON_PROGRESS = "on_progress"
CONF_ON_END = "on_end"
CONF_ON_ERROR = "on_error"

ota_ns = cg.esphome_ns.namespace("ota")
OTAState = ota_ns.enum("OTAState")
OTAComponent = ota_ns.class_("OTAComponent", cg.Component)
OTAStateChangeTrigger = ota_ns.class_(
    "OTAStateChangeTrigger", automation.Trigger.template()
)
OTAStartTrigger = ota_ns.class_("OTAStartTrigger", automation.Trigger.template())
OTAProgressTrigger = ota_ns.class_("OTAProgressTrigger", automation.Trigger.template())
OTAEndTrigger = ota_ns.class_("OTAEndTrigger", automation.Trigger.template())
OTAErrorTrigger = ota_ns.class_("OTAErrorTrigger", automation.Trigger.template())


def validate_config(config):
    if config[CONF_UNPROTECTED_WRITES] and not CORE.is_esp32:
        raise cv.Invalid(f"{CONF_UNPROTECTED_WRITES} is only supported on the esp32")

    return config


CONFIG_SCHEMA = cv.All(
    cv.Schema(
        {
            cv.GenerateID(): cv.declare_id(OTAComponent),
            cv.Optional(CONF_SAFE_MODE, default=False): cv.boolean,
            cv.Optional(CONF_UNPROTECTED_WRITES, default=False): cv.boolean,
            cv.Optional(CONF_PASSWORD): cv.string,
            cv.Optional(
                CONF_REBOOT_TIMEOUT, default="5min"
            ): cv.positive_time_period_milliseconds,
            cv.Optional(CONF_NUM_ATTEMPTS, default="10"): cv.positive_not_null_int,
            cv.Optional(CONF_ON_STATE_CHANGE): automation.validate_automation(
                {
                    cv.GenerateID(CONF_TRIGGER_ID): cv.declare_id(
                        OTAStateChangeTrigger
                    ),
                }
            ),
            cv.Optional(CONF_ON_BEGIN): automation.validate_automation(
                {
                    cv.GenerateID(CONF_TRIGGER_ID): cv.declare_id(OTAStartTrigger),
                }
            ),
            cv.Optional(CONF_ON_ERROR): automation.validate_automation(
                {
                    cv.GenerateID(CONF_TRIGGER_ID): cv.declare_id(OTAErrorTrigger),
                }
            ),
            cv.Optional(CONF_ON_PROGRESS): automation.validate_automation(
                {
                    cv.GenerateID(CONF_TRIGGER_ID): cv.declare_id(OTAProgressTrigger),
                }
            ),
            cv.Optional(CONF_ON_END): automation.validate_automation(
                {
                    cv.GenerateID(CONF_TRIGGER_ID): cv.declare_id(OTAEndTrigger),
                }
            ),
        }
    ).extend(cv.COMPONENT_SCHEMA),
    validate_config,
)


@coroutine_with_priority(50.0)
async def to_code(config):
    CORE.data[CONF_OTA] = {}

    var = cg.new_Pvariable(config[CONF_ID])
    cg.add_define("USE_OTA")
    if CONF_PASSWORD in config:
        cg.add(var.set_auth_password(config[CONF_PASSWORD]))
        cg.add_define("USE_OTA_PASSWORD")
    if config[CONF_UNPROTECTED_WRITES]:
        cg.add_build_flag("-DCONFIG_SPI_FLASH_DANGEROUS_WRITE_ALLOWED=1")
        cg.add_define("USE_UNPROTECTED_WRITES")

    await cg.register_component(var, config)

    if config[CONF_SAFE_MODE]:
        condition = var.should_enter_safe_mode(
            config[CONF_NUM_ATTEMPTS], config[CONF_REBOOT_TIMEOUT]
        )
        cg.add(RawExpression(f"if ({condition}) return"))
        CORE.data[CONF_OTA][KEY_PAST_SAFE_MODE] = True

    if CORE.is_rp2040 and CORE.using_arduino:
        cg.add_library("Updater", None)

    use_state_callback = False
    for conf in config.get(CONF_ON_STATE_CHANGE, []):
        trigger = cg.new_Pvariable(conf[CONF_TRIGGER_ID], var)
        await automation.build_automation(trigger, [(OTAState, "state")], conf)
        use_state_callback = True
    for conf in config.get(CONF_ON_BEGIN, []):
        trigger = cg.new_Pvariable(conf[CONF_TRIGGER_ID], var)
        await automation.build_automation(trigger, [], conf)
        use_state_callback = True
    for conf in config.get(CONF_ON_PROGRESS, []):
        trigger = cg.new_Pvariable(conf[CONF_TRIGGER_ID], var)
        await automation.build_automation(trigger, [(float, "x")], conf)
        use_state_callback = True
    for conf in config.get(CONF_ON_END, []):
        trigger = cg.new_Pvariable(conf[CONF_TRIGGER_ID], var)
        await automation.build_automation(trigger, [], conf)
        use_state_callback = True
    for conf in config.get(CONF_ON_ERROR, []):
        trigger = cg.new_Pvariable(conf[CONF_TRIGGER_ID], var)
        await automation.build_automation(trigger, [(cg.uint8, "x")], conf)
        use_state_callback = True
    if use_state_callback:
        cg.add_define("USE_OTA_STATE_CALLBACK")

package xiaozhi.modules.device.controller;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.apache.shiro.authz.annotation.RequiresPermissions;
import org.springframework.web.bind.annotation.*;
import xiaozhi.common.user.UserDetail;
import xiaozhi.common.utils.Result;
import xiaozhi.modules.device.dto.SendMessageDTO;
import xiaozhi.modules.device.entity.DeviceMessageEntity;
import xiaozhi.modules.device.service.DeviceMessageService;
import xiaozhi.modules.security.user.SecurityUser;

import java.util.List;

@Tag(name = "设备消息管理")
@RestController
@RequestMapping("/device/message")
public class DeviceMessageController {

    private final DeviceMessageService deviceMessageService;

    public DeviceMessageController(DeviceMessageService deviceMessageService) {
        this.deviceMessageService = deviceMessageService;
    }

    @PostMapping("/send")
    @Operation(summary = "发送消息")
    @RequiresPermissions("sys:role:normal")
    public Result<Void> sendMessage(@Valid @RequestBody SendMessageDTO dto) {
        UserDetail user = SecurityUser.getUser();
        deviceMessageService.sendMessage(dto, user.getId());
        return new Result<>();
    }

    @GetMapping("/history")
    @Operation(summary = "获取消息记录")
    @RequiresPermissions("sys:role:normal")
    public Result<List<DeviceMessageEntity>> getMessageHistory(@RequestParam String deviceId, @RequestParam String friendDeviceId) {
        UserDetail user = SecurityUser.getUser();
        List<DeviceMessageEntity> list = deviceMessageService.getMessageHistory(deviceId, friendDeviceId, user.getId());
        return new Result<List<DeviceMessageEntity>>().ok(list);
    }

    @PostMapping("/read")
    @Operation(summary = "标记已读")
    @RequiresPermissions("sys:role:normal")
    public Result<Void> markAsRead(@RequestParam String deviceId, @RequestParam String friendDeviceId) {
        UserDetail user = SecurityUser.getUser();
        deviceMessageService.markAsRead(deviceId, friendDeviceId, user.getId());
        return new Result<>();
    }
}

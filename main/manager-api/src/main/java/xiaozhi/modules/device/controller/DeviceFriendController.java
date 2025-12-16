package xiaozhi.modules.device.controller;

import java.util.List;

import org.apache.shiro.authz.annotation.RequiresPermissions;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import xiaozhi.common.user.UserDetail;
import xiaozhi.common.utils.Result;
import xiaozhi.modules.device.dto.AddDeviceFriendDTO;
import xiaozhi.modules.device.dto.HandleFriendRequestDTO;
import xiaozhi.modules.device.entity.DeviceFriendEntity;
import xiaozhi.modules.device.service.DeviceFriendService;
import xiaozhi.modules.device.vo.SearchDeviceResultVO;
import xiaozhi.modules.security.user.SecurityUser;

@Tag(name = "设备交友管理")
@RestController
@RequestMapping("/device/friend")
public class DeviceFriendController {

    private final DeviceFriendService deviceFriendService;

    public DeviceFriendController(DeviceFriendService deviceFriendService) {
        this.deviceFriendService = deviceFriendService;
    }

    @GetMapping("/search")
    @Operation(summary = "搜索设备")
    @RequiresPermissions("sys:role:normal")
    public Result<List<SearchDeviceResultVO>> searchDevice(@RequestParam String keyword) {
        List<SearchDeviceResultVO> results = deviceFriendService.searchDevice(keyword);
        return new Result<List<SearchDeviceResultVO>>().ok(results);
    }

    @PostMapping("/add")
    @Operation(summary = "添加好友")
    @RequiresPermissions("sys:role:normal")
    public Result<Void> addFriend(@Valid @RequestBody AddDeviceFriendDTO dto) {
        UserDetail user = SecurityUser.getUser();
        deviceFriendService.addFriend(dto, user.getId());
        return new Result<>();
    }

    @GetMapping("/list/{deviceId}")
    @Operation(summary = "获取好友列表")
    @RequiresPermissions("sys:role:normal")
    public Result<List<DeviceFriendEntity>> getFriendList(@PathVariable String deviceId) {
        UserDetail user = SecurityUser.getUser();
        List<DeviceFriendEntity> friends = deviceFriendService.getFriendList(deviceId, user.getId());
        return new Result<List<DeviceFriendEntity>>().ok(friends);
    }

    @GetMapping("/requests/{deviceId}")
    @Operation(summary = "获取好友请求列表")
    @RequiresPermissions("sys:role:normal")
    public Result<List<DeviceFriendEntity>> getFriendRequests(@PathVariable String deviceId) {
        UserDetail user = SecurityUser.getUser();
        List<DeviceFriendEntity> requests = deviceFriendService.getFriendRequests(deviceId, user.getId());
        return new Result<List<DeviceFriendEntity>>().ok(requests);
    }

    @PostMapping("/handle")
    @Operation(summary = "处理好友请求")
    @RequiresPermissions("sys:role:normal")
    public Result<Void> handleFriendRequest(@Valid @RequestBody HandleFriendRequestDTO dto) {
        UserDetail user = SecurityUser.getUser();
        deviceFriendService.handleFriendRequest(dto, user.getId());
        return new Result<>();
    }

    @DeleteMapping("/{friendId}")
    @Operation(summary = "删除好友")
    @RequiresPermissions("sys:role:normal")
    public Result<Void> deleteFriend(@PathVariable String friendId) {
        UserDetail user = SecurityUser.getUser();
        deviceFriendService.deleteFriend(friendId, user.getId());
        return new Result<>();
    }
}

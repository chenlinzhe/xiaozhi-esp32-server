package xiaozhi.modules.device.service;

import java.util.List;

import xiaozhi.modules.device.dto.AddDeviceFriendDTO;
import xiaozhi.modules.device.dto.HandleFriendRequestDTO;
import xiaozhi.modules.device.entity.DeviceFriendEntity;
import xiaozhi.modules.device.vo.SearchDeviceResultVO;

public interface DeviceFriendService {

    /**
     * 搜索设备(通过用户名或MAC地址)
     *
     * @param keyword 关键词
     * @return 搜索结果列表
     */
    List<SearchDeviceResultVO> searchDevice(String keyword);

    /**
     * 添加好友
     *
     * @param dto 添加好友请求
     * @param userId 当前用户ID
     */
    void addFriend(AddDeviceFriendDTO dto, Long userId);

    /**
     * 获取好友列表
     *
     * @param deviceId 设备ID
     * @param userId 当前用户ID
     * @return 好友列表
     */
    List<DeviceFriendEntity> getFriendList(String deviceId, Long userId);

    /**
     * 获取好友请求列表
     *
     * @param deviceId 设备ID
     * @param userId 当前用户ID
     * @return 好友请求列表
     */
    List<DeviceFriendEntity> getFriendRequests(String deviceId, Long userId);

    /**
     * 处理好友请求
     *
     * @param dto 处理请求DTO
     * @param userId 当前用户ID
     */
    void handleFriendRequest(HandleFriendRequestDTO dto, Long userId);

    /**
     * 删除好友
     *
     * @param friendId 好友关系ID
     * @param userId 当前用户ID
     */
    void deleteFriend(String friendId, Long userId);
}

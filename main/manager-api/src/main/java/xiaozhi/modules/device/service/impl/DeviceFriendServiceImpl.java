package xiaozhi.modules.device.service.impl;

import java.util.ArrayList;
import java.util.List;

import org.apache.commons.lang3.StringUtils;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;

import xiaozhi.common.exception.ErrorCode;
import xiaozhi.common.exception.RenException;
import xiaozhi.modules.agent.entity.AgentEntity;
import xiaozhi.modules.agent.service.AgentService;
import xiaozhi.modules.device.dao.DeviceDao;
import xiaozhi.modules.device.dao.DeviceFriendDao;
import xiaozhi.modules.device.dto.AddDeviceFriendDTO;
import xiaozhi.modules.device.dto.HandleFriendRequestDTO;
import xiaozhi.modules.device.entity.DeviceEntity;
import xiaozhi.modules.device.entity.DeviceFriendEntity;
import xiaozhi.modules.device.service.DeviceFriendService;
import xiaozhi.modules.device.vo.SearchDeviceResultVO;
import xiaozhi.modules.sys.service.SysUserService;
import xiaozhi.modules.sys.dto.SysUserDTO;
import xiaozhi.common.user.UserDetail;

@Service
public class DeviceFriendServiceImpl implements DeviceFriendService {

    private final DeviceFriendDao deviceFriendDao;
    private final DeviceDao deviceDao;
    private final AgentService agentService;
    private final SysUserService sysUserService;

    public DeviceFriendServiceImpl(DeviceFriendDao deviceFriendDao, DeviceDao deviceDao,
            AgentService agentService, SysUserService sysUserService) {
        this.deviceFriendDao = deviceFriendDao;
        this.deviceDao = deviceDao;
        this.agentService = agentService;
        this.sysUserService = sysUserService;
    }

    @Override
    public List<SearchDeviceResultVO> searchDevice(String keyword) {
        if (StringUtils.isBlank(keyword)) {
            return new ArrayList<>();
        }

        List<SearchDeviceResultVO> results = new ArrayList<>();

        // 尝试按用户名搜索
        SysUserDTO userDTO = sysUserService.getByUsername(keyword);
        UserDetail user = userDTO != null ? convertToUserDetail(userDTO) : null;
        if (user != null) {
            // 获取该用户的设备
            QueryWrapper<DeviceEntity> deviceQuery = new QueryWrapper<>();
            deviceQuery.eq("user_id", user.getId());
            List<DeviceEntity> devices = deviceDao.selectList(deviceQuery);

            for (DeviceEntity device : devices) {
                SearchDeviceResultVO vo = buildSearchResult(device, user);
                if (vo != null) {
                    results.add(vo);
                }
            }
        }

        // 尝试按MAC地址搜索
        QueryWrapper<DeviceEntity> macQuery = new QueryWrapper<>();
        macQuery.like("mac_address", keyword);
        List<DeviceEntity> devicesByMac = deviceDao.selectList(macQuery);

        for (DeviceEntity device : devicesByMac) {
            SysUserDTO deviceUserDTO = sysUserService.getByUserId(device.getUserId());
            UserDetail deviceUser = deviceUserDTO != null ? convertToUserDetail(deviceUserDTO) : null;
            SearchDeviceResultVO vo = buildSearchResult(device, deviceUser);
            if (vo != null && !results.stream().anyMatch(r -> r.getDeviceId().equals(vo.getDeviceId()))) {
                results.add(vo);
            }
        }

        return results;
    }

    private SearchDeviceResultVO buildSearchResult(DeviceEntity device, UserDetail user) {
        if (device == null || user == null) {
            return null;
        }

        SearchDeviceResultVO vo = new SearchDeviceResultVO();
        vo.setDeviceId(device.getId());
        vo.setMacAddress(device.getMacAddress());
        vo.setUsername(user.getUsername());
        vo.setAgentId(device.getAgentId());

        // 获取智能体名称
        if (StringUtils.isNotBlank(device.getAgentId())) {
            AgentEntity agent = agentService.getAgentById(device.getAgentId());
            vo.setAgentName(agent != null ? agent.getAgentName() : "");
        }

        return vo;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void addFriend(AddDeviceFriendDTO dto, Long userId) {
        // 验证设备归属
        DeviceEntity device = deviceDao.selectById(dto.getDeviceId());
        if (device == null || !device.getUserId().equals(userId)) {
            throw new RenException(ErrorCode.FORBIDDEN, "设备不存在或无权操作");
        }

        // 查找目标设备
        DeviceEntity friendDevice = null;
        
        // 尝试按MAC地址查找
        QueryWrapper<DeviceEntity> query = new QueryWrapper<>();
        query.eq("mac_address", dto.getFriendIdentifier());
        friendDevice = deviceDao.selectOne(query);

        // 如果没找到，尝试按用户名查找
        if (friendDevice == null) {
            SysUserDTO friendUserDTO = sysUserService.getByUsername(dto.getFriendIdentifier());
            UserDetail friendUser = friendUserDTO != null ? convertToUserDetail(friendUserDTO) : null;
            if (friendUser != null) {
                QueryWrapper<DeviceEntity> userDeviceQuery = new QueryWrapper<>();
                userDeviceQuery.eq("user_id", friendUser.getId());
                List<DeviceEntity> userDevices = deviceDao.selectList(userDeviceQuery);
                if (!userDevices.isEmpty()) {
                    friendDevice = userDevices.get(0); // 取第一个设备
                }
            }
        }

        if (friendDevice == null) {
            throw new RenException(ErrorCode.RESOURCE_NOT_FOUND, "未找到目标设备");
        }

        // 不能添加自己为好友
        if (friendDevice.getId().equals(dto.getDeviceId())) {
            throw new RenException(ErrorCode.PARAMS_GET_ERROR, "不能添加自己为好友");
        }

        // 检查是否已经是好友或已发送请求
        QueryWrapper<DeviceFriendEntity> existQuery = new QueryWrapper<>();
        existQuery.eq("device_id", dto.getDeviceId())
                  .eq("friend_device_id", friendDevice.getId());
        DeviceFriendEntity existFriend = deviceFriendDao.selectOne(existQuery);
        
        if (existFriend != null) {
            if (existFriend.getStatus() == 0) {
                throw new RenException(ErrorCode.DB_RECORD_EXISTS, "已发送好友请求，请等待对方确认");
            } else if (existFriend.getStatus() == 1) {
                throw new RenException(ErrorCode.DB_RECORD_EXISTS, "已经是好友");
            }
        }

        // 创建好友请求
        DeviceFriendEntity friendEntity = new DeviceFriendEntity();
        friendEntity.setDeviceId(dto.getDeviceId());
        friendEntity.setFriendDeviceId(friendDevice.getId());
        friendEntity.setFriendMacAddress(friendDevice.getMacAddress());
        
        // 获取好友用户名
        SysUserDTO friendUserDTO = sysUserService.getByUserId(friendDevice.getUserId());
        UserDetail friendUser = friendUserDTO != null ? convertToUserDetail(friendUserDTO) : null;
        friendEntity.setFriendUsername(friendUser != null ? friendUser.getUsername() : "");
        
        // 获取好友智能体名称
        if (StringUtils.isNotBlank(friendDevice.getAgentId())) {
            AgentEntity agent = agentService.getAgentById(friendDevice.getAgentId());
            friendEntity.setFriendAgentName(agent != null ? agent.getAgentName() : "");
        }
        
        friendEntity.setStatus(0); // 待确认
        deviceFriendDao.insert(friendEntity);
    }

    @Override
    public List<DeviceFriendEntity> getFriendList(String deviceId, Long userId) {
        // 验证设备归属
        DeviceEntity device = deviceDao.selectById(deviceId);
        if (device == null || !device.getUserId().equals(userId)) {
            throw new RenException(ErrorCode.FORBIDDEN, "设备不存在或无权操作");
        }

        QueryWrapper<DeviceFriendEntity> query = new QueryWrapper<>();
        query.eq("device_id", deviceId)
             .eq("status", 1) // 已同意
             .orderByDesc("create_date");
        
        return deviceFriendDao.selectList(query);
    }

    @Override
    public List<DeviceFriendEntity> getFriendRequests(String deviceId, Long userId) {
        // 验证设备归属
        DeviceEntity device = deviceDao.selectById(deviceId);
        if (device == null || !device.getUserId().equals(userId)) {
            throw new RenException(ErrorCode.FORBIDDEN, "设备不存在或无权操作");
        }

        // 查找别人发送给我的好友请求
        QueryWrapper<DeviceFriendEntity> query = new QueryWrapper<>();
        query.eq("friend_device_id", deviceId)
             .eq("status", 0) // 待确认
             .orderByDesc("create_date");
        
        return deviceFriendDao.selectList(query);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void handleFriendRequest(HandleFriendRequestDTO dto, Long userId) {
        DeviceFriendEntity request = deviceFriendDao.selectById(dto.getRequestId());
        if (request == null) {
            throw new RenException(ErrorCode.RESOURCE_NOT_FOUND, "好友请求不存在");
        }

        // 验证是否是请求的接收方
        DeviceEntity friendDevice = deviceDao.selectById(request.getFriendDeviceId());
        if (friendDevice == null || !friendDevice.getUserId().equals(userId)) {
            throw new RenException(ErrorCode.FORBIDDEN, "无权操作此请求");
        }

        if ("accept".equals(dto.getAction())) {
            // 同意好友请求
            System.out.println("[DEBUG] 接受好友请求: requestId=" + dto.getRequestId() + ", userId=" + userId);
            
            // 1. 更新原请求状态为已同意
            request.setStatus(1);
            int updated = deviceFriendDao.updateById(request);
            System.out.println("[DEBUG] 更新原请求状态: affected=" + updated);

            // 2. 创建反向好友关系
            DeviceEntity originDevice = deviceDao.selectById(request.getDeviceId());
            if (originDevice == null) {
                throw new RenException(ErrorCode.RESOURCE_NOT_FOUND, "原始设备不存在");
            }
            
            SysUserDTO originUserDTO = sysUserService.getByUserId(originDevice.getUserId());
            UserDetail originUser = originUserDTO != null ? convertToUserDetail(originUserDTO) : null;
            
            DeviceFriendEntity reverseFriend = new DeviceFriendEntity();
            reverseFriend.setDeviceId(request.getFriendDeviceId());
            reverseFriend.setFriendDeviceId(request.getDeviceId());
            reverseFriend.setFriendMacAddress(originDevice.getMacAddress());
            reverseFriend.setFriendUsername(originUser != null ? originUser.getUsername() : "");
            
            // 获取智能体名称
            if (StringUtils.isNotBlank(originDevice.getAgentId())) {
                AgentEntity agent = agentService.getAgentById(originDevice.getAgentId());
                reverseFriend.setFriendAgentName(agent != null ? agent.getAgentName() : "");
            } else {
                reverseFriend.setFriendAgentName("");
            }
            
            reverseFriend.setStatus(1); // 直接设为已同意
            int inserted = deviceFriendDao.insert(reverseFriend);
            System.out.println("[DEBUG] 创建反向好友关系: affected=" + inserted + ", friendDeviceId=" + reverseFriend.getFriendDeviceId());
            
        } else if ("reject".equals(dto.getAction())) {
            // 拒绝好友请求 - 直接删除
            System.out.println("[DEBUG] 拒绝好友请求: requestId=" + dto.getRequestId());
            int deleted = deviceFriendDao.deleteById(dto.getRequestId());
            System.out.println("[DEBUG] 删除请求: affected=" + deleted);
        } else {
            throw new RenException(ErrorCode.PARAMS_GET_ERROR, "无效的操作类型");
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void deleteFriend(String friendId, Long userId) {
        DeviceFriendEntity friend = deviceFriendDao.selectById(friendId);
        if (friend == null) {
            throw new RenException(ErrorCode.RESOURCE_NOT_FOUND, "好友关系不存在");
        }

        // 验证设备归属
        DeviceEntity device = deviceDao.selectById(friend.getDeviceId());
        if (device == null || !device.getUserId().equals(userId)) {
            throw new RenException(ErrorCode.FORBIDDEN, "无权操作");
        }

        // 删除好友关系
        deviceFriendDao.deleteById(friendId);

        // 删除反向好友关系
        QueryWrapper<DeviceFriendEntity> query = new QueryWrapper<>();
        query.eq("device_id", friend.getFriendDeviceId())
             .eq("friend_device_id", friend.getDeviceId());
        deviceFriendDao.delete(query);
    }

    /**
     * 将SysUserDTO转换为UserDetail
     */
    private UserDetail convertToUserDetail(SysUserDTO dto) {
        if (dto == null) {
            return null;
        }
        UserDetail userDetail = new UserDetail();
        userDetail.setId(dto.getId());
        userDetail.setUsername(dto.getUsername());
        userDetail.setStatus(dto.getStatus());
        userDetail.setSuperAdmin(dto.getSuperAdmin());
        return userDetail;
    }
}

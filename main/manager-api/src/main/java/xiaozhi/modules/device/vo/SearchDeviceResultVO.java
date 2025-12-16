package xiaozhi.modules.device.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Data
@Schema(description = "搜索设备结果VO")
public class SearchDeviceResultVO {

    @Schema(description = "设备ID")
    private String deviceId;

    @Schema(description = "MAC地址")
    private String macAddress;

    @Schema(description = "用户名")
    private String username;

    @Schema(description = "智能体ID")
    private String agentId;

    @Schema(description = "智能体名称")
    private String agentName;
}

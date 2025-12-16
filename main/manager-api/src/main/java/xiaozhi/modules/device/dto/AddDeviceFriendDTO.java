package xiaozhi.modules.device.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
@Schema(description = "添加好友请求DTO")
public class AddDeviceFriendDTO {

    @NotBlank(message = "设备ID不能为空")
    @Schema(description = "设备ID")
    private String deviceId;

    @NotBlank(message = "好友标识不能为空")
    @Schema(description = "好友标识(用户名或MAC地址)")
    private String friendIdentifier;
}

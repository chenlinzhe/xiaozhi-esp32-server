package xiaozhi.modules.device.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

import java.io.Serializable;

@Data
@Schema(description = "发送设备消息")
public class SendMessageDTO implements Serializable {
    @Schema(description = "发送方设备ID", required = true)
    @NotBlank(message = "发送方设备ID不能为空")
    private String fromDeviceId;

    @Schema(description = "接收方设备ID", required = true)
    @NotBlank(message = "接收方设备ID不能为空")
    private String toDeviceId;

    @Schema(description = "消息内容", required = true)
    @NotBlank(message = "消息内容不能为空")
    private String content;

    @Schema(description = "消息类型 0:文本 1:图片 2:语音")
    private Integer type = 0;
}

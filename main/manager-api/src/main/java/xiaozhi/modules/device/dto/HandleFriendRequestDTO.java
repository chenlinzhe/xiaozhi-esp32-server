package xiaozhi.modules.device.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

@Data
@Schema(description = "处理好友请求DTO")
public class HandleFriendRequestDTO {

    @NotBlank(message = "请求ID不能为空")
    @Schema(description = "请求ID")
    private String requestId;

    @NotBlank(message = "操作类型不能为空")
    @Schema(description = "操作类型: accept-同意, reject-拒绝")
    private String action;
}

package xiaozhi.common.convert;

import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.databind.DeserializationContext;
import com.fasterxml.jackson.databind.JsonDeserializer;

import java.io.IOException;

/**
 * 布尔值转整数的反序列化器
 * true -> 1, false -> 0
 * 
 * @author xiaozhi
 * @since 2024-12-01
 */
public class BooleanToIntegerDeserializer extends JsonDeserializer<Integer> {

    @Override
    public Integer deserialize(JsonParser p, DeserializationContext ctxt) throws IOException {
        if (p.getCurrentToken().isBoolean()) {
            return p.getBooleanValue() ? 1 : 0;
        } else if (p.getCurrentToken().isNumeric()) {
            return p.getIntValue();
        } else if (p.getCurrentToken().asString() != null) {
            String value = p.getText();
            if ("true".equalsIgnoreCase(value) || "1".equals(value)) {
                return 1;
            } else if ("false".equalsIgnoreCase(value) || "0".equals(value)) {
                return 0;
            }
        }
        return null;
    }
}

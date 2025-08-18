//首先实现与OTA服务器的交互，获取WebSocket配置：

class OtaClient {
    private val otaUrl = "https:/XXXozhi/ota/"
    private val httpClient = OkHttpClient()

    data class DeviceInfo(
        val deviceId: String,
        val clientId: String,
        val version: String
    )

    data class WebSocketConfig(
        val url: String,
        val token: String?,
        val version: Int
    )

    suspend fun checkVersion(deviceInfo: DeviceInfo): WebSocketConfig? {
        val request = Request.Builder()
            .url(otaUrl)
            .addHeader("Device-Id", deviceInfo.deviceId)
            .addHeader("Client-Id", deviceInfo.clientId)
            .addHeader("User-Agent", "AndroidClient/${deviceInfo.version}")
            .addHeader("Content-Type", "application/json")
            .post(createDeviceInfoJson(deviceInfo).toRequestBody("application/json".toMediaType()))
            .build()

        return withContext(Dispatchers.IO) {
            try {
                val response = httpClient.newCall(request).execute()
                if (response.isSuccessful) {
                    parseWebSocketConfig(response.body?.string())
                } else null
            } catch (e: Exception) {
                null
            }
        }
    }

    private fun parseWebSocketConfig(responseBody: String?): WebSocketConfig? {
        return try {
            val json = JSONObject(responseBody ?: return null)
            val websocket = json.optJSONObject("websocket") ?: return null

            WebSocketConfig(
                url = websocket.optString("url"),
                token = websocket.optString("token"),
                version = websocket.optInt("version", 1)
            )
        } catch (e: Exception) {
            null
        }
    }
}


//接下来实现WebSocket通信协议：


class XiaoZhiWebSocketClient(
    private val config: WebSocketConfig,
    private val audioHandler: (ByteArray) -> Unit,
    private val messageHandler: (JSONObject) -> Unit
) {
    private var webSocket: WebSocket? = null
    private val client = OkHttpClient()

    fun connect() {
        val request = Request.Builder()
            .url(config.url)
            .apply {
                config.token?.let { token ->
                    val authToken = if (token.contains(" ")) token else "Bearer $token"
                    addHeader("Authorization", authToken)
                }
            }
            .addHeader("Protocol-Version", config.version.toString())
            .addHeader("Device-Id", getDeviceId())
            .addHeader("Client-Id", getClientId())
            .build()

        webSocket = client.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                sendHelloMessage()
            }

            override fun onMessage(webSocket: WebSocket, text: String) {
                handleTextMessage(text)
            }

            override fun onMessage(webSocket: WebSocket, bytes: ByteString) {
                handleBinaryMessage(bytes.toByteArray())
            }
        })
    }

    private fun sendHelloMessage() {
        val hello = JSONObject().apply {
            put("type", "hello")
            put("version", config.version)
            put("transport", "websocket")
            put("features", JSONObject().apply {
                put("aec", true)
                put("mcp", true)
            })
            put("audio_params", JSONObject().apply {
                put("format", "opus")
                put("sample_rate", 16000)
                put("channels", 1)
                put("frame_duration", 60)
            })
        }
        webSocket?.send(hello.toString())
    }

    private fun handleBinaryMessage(data: ByteArray) {
        when (config.version) {
            2 -> {
                // BinaryProtocol2 format
                if (data.size >= 16) {
                    val payloadSize = ByteBuffer.wrap(data, 12, 4).int
                    val payload = data.copyOfRange(16, 16 + payloadSize)
                    audioHandler(payload)
                }
            }
            3 -> {
                // BinaryProtocol3 format
                if (data.size >= 4) {
                    val payloadSize = ByteBuffer.wrap(data, 2, 2).short.toInt()
                    val payload = data.copyOfRange(4, 4 + payloadSize)
                    audioHandler(payload)
                }
            }
            else -> {
                // Version 1 - raw audio data
                audioHandler(data)
            }
        }
    }

    private fun handleTextMessage(text: String) {
        try {
            val json = JSONObject(text)
            val type = json.optString("type")

            if (type == "hello") {
                handleServerHello(json)
            } else {
                messageHandler(json)
            }
        } catch (e: Exception) {
            // Handle parsing error
        }
    }

    fun sendAudio(audioData: ByteArray) {
        when (config.version) {
            2 -> {
                val packet = ByteBuffer.allocate(16 + audioData.size).apply {
                    putShort(config.version.toShort())
                    putShort(1) // audio type
                    putInt(0) // reserved
                    putInt(System.currentTimeMillis().toInt())
                    putInt(audioData.size)
                    put(audioData)
                }
                webSocket?.send(ByteString.of(*packet.array()))
            }
            3 -> {
                val packet = ByteBuffer.allocate(4 + audioData.size).apply {
                    put(1) // audio type
                    put(0) // reserved
                    putShort(audioData.size.toShort())
                    put(audioData)
                }
                webSocket?.send(ByteString.of(*packet.array()))
            }
            else -> {
                webSocket?.send(ByteString.of(*audioData))
            }
        }
    }
}


//最后是应用层的集成代码：

class XiaoZhiAndroidClient {
    private val otaClient = OtaClient()
    private var webSocketClient: XiaoZhiWebSocketClient? = null

    suspend fun initialize() {
        val deviceInfo = OtaClient.DeviceInfo(
            deviceId = getDeviceId(),
            clientId = UUID.randomUUID().toString(),
            version = "1.0.0"
        )

        val config = otaClient.checkVersion(deviceInfo)
        if (config != null) {
            webSocketClient = XiaoZhiWebSocketClient(
                config = config,
                audioHandler = { audioData ->
                    // 处理接收到的音频数据
                    playAudio(audioData)
                },
                messageHandler = { message ->
                    // 处理接收到的JSON消息
                    handleServerMessage(message)
                }
            )
            webSocketClient?.connect()
        }
    }
}







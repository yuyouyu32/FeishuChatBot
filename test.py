import lark_oapi as lark
from lark_oapi.api.im.v1 import *


# SDK 使用说明: https://github.com/larksuite/oapi-sdk-python#readme
# 复制该 Demo 后, 需要将 "APP_ID", "APP_SECRET" 替换为自己应用的 APP_ID, APP_SECRET.
def main():
    # 创建client
    client = lark.Client.builder() \
        .app_id("cli_a58bccc50c30d00c") \
        .app_secret("Rnx4qw4aoEjpa8WGCv3h5whlBTvC8KVA") \
        .log_level(lark.LogLevel.DEBUG) \
        .build()

    # 构造请求对象
    request: CreateMessageRequest = CreateMessageRequest.builder() \
        .receive_id_type("user_id") \
        .request_body(CreateMessageRequestBody.builder()
            .receive_id("ou_7d8a6e6df7621556ce0d21922b676706ccs")
            .msg_type("text")
            .content("{\"text\":\"test content\"}")
            # .uuid("a0d69e20-1dd1-458b-k525-dfeca4015204")
            .build()) \
        .build()

    # 发起请求
    response: CreateMessageResponse = client.im.v1.message.create(request)

    # 处理失败返回
    if not response.success():
        lark.logger.error(
            f"client.im.v1.message.create failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}")
        return

    # 处理业务结果
    lark.logger.info(lark.JSON.marshal(response.data, indent=4))


if __name__ == "__main__":
    main()
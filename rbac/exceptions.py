"""
自定义异常处理器
"""
from rest_framework.views import exception_handler
from rest_framework import status
from django.http import JsonResponse
from .response import ApiResponse, ResponseCode
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """自定义异常处理器"""
    
    # 调用DRF默认的异常处理器
    response = exception_handler(exc, context)
    
    if response is not None:
        # 记录异常日志
        logger.warning(f"API异常: {exc}, 视图: {context.get('view', 'Unknown')}")
        
        # 获取原始错误数据
        error_data = response.data
        status_code = response.status_code
        
        # 根据不同的状态码返回统一格式
        if status_code == status.HTTP_401_UNAUTHORIZED:
            return ApiResponse.unauthorized()
        elif status_code == status.HTTP_403_FORBIDDEN:
            return ApiResponse.forbidden()
        elif status_code == status.HTTP_404_NOT_FOUND:
            return ApiResponse.not_found()
        elif status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
            return ApiResponse.method_not_allowed()
        elif status_code == status.HTTP_400_BAD_REQUEST:
            # 处理验证错误
            if isinstance(error_data, dict):
                if 'detail' in error_data:
                    message = error_data['detail']
                    return ApiResponse.error(message=message, http_status=status_code)
                else:
                    # 字段验证错误
                    return ApiResponse.validation_error(errors=error_data)
            else:
                return ApiResponse.error(message=str(error_data), http_status=status_code)
        elif 400 <= status_code < 500:
            # 其他客户端错误
            message = error_data.get('detail', '客户端请求错误') if isinstance(error_data, dict) else str(error_data)
            return ApiResponse.error(message=message, http_status=status_code)
        else:
            # 服务器错误
            logger.error(f"服务器错误: {exc}", exc_info=True)
            return ApiResponse.server_error()
    
    # 如果不是DRF能处理的异常，记录并返回服务器错误
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    return ApiResponse.server_error()


class ApiException(Exception):
    """自定义API异常"""
    
    def __init__(self, message="操作失败", code=ResponseCode.ERROR, status_code=status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)
    
    def to_response(self):
        """转换为响应"""
        return ApiResponse.error(
            message=self.message,
            code=self.code,
            http_status=self.status_code
        )

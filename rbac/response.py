"""
统一响应封装
"""
from django.http import JsonResponse
from rest_framework import status
from typing import Any, Optional, Dict


class ResponseCode:
    """响应状态码"""
    SUCCESS = 0
    ERROR = 1
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    VALIDATION_ERROR = 422
    SERVER_ERROR = 500


class ApiResponse:
    """统一API响应封装"""
    
    @staticmethod
    def success(data: Any = None, message: str = "操作成功", code: int = ResponseCode.SUCCESS) -> JsonResponse:
        """成功响应"""
        response_data = {
            "code": code,
            "message": message,
            "data": data,
            "success": True
        }
        return JsonResponse(response_data, status=status.HTTP_200_OK)
    
    @staticmethod
    def error(message: str = "操作失败", code: int = ResponseCode.ERROR, 
              data: Any = None, http_status: int = status.HTTP_400_BAD_REQUEST) -> JsonResponse:
        """错误响应"""
        response_data = {
            "code": code,
            "message": message,
            "data": data,
            "success": False
        }
        return JsonResponse(response_data, status=http_status)
    
    @staticmethod
    def unauthorized(message: str = "未登录或token已过期") -> JsonResponse:
        """未授权响应"""
        return ApiResponse.error(
            message=message,
            code=ResponseCode.UNAUTHORIZED,
            http_status=status.HTTP_401_UNAUTHORIZED
        )
    
    @staticmethod
    def forbidden(message: str = "权限不足") -> JsonResponse:
        """禁止访问响应"""
        return ApiResponse.error(
            message=message,
            code=ResponseCode.FORBIDDEN,
            http_status=status.HTTP_403_FORBIDDEN
        )
    
    @staticmethod
    def not_found(message: str = "资源不存在") -> JsonResponse:
        """资源不存在响应"""
        return ApiResponse.error(
            message=message,
            code=ResponseCode.NOT_FOUND,
            http_status=status.HTTP_404_NOT_FOUND
        )
    
    @staticmethod
    def method_not_allowed(message: str = "请求方法不允许") -> JsonResponse:
        """请求方法不允许响应"""
        return ApiResponse.error(
            message=message,
            code=ResponseCode.METHOD_NOT_ALLOWED,
            http_status=status.HTTP_405_METHOD_NOT_ALLOWED
        )
    
    @staticmethod
    def validation_error(message: str = "参数验证失败", errors: Dict = None) -> JsonResponse:
        """参数验证错误响应"""
        data = {"errors": errors} if errors else None
        return ApiResponse.error(
            message=message,
            code=ResponseCode.VALIDATION_ERROR,
            data=data,
            http_status=status.HTTP_422_UNPROCESSABLE_ENTITY
        )
    
    @staticmethod
    def server_error(message: str = "服务器内部错误") -> JsonResponse:
        """服务器错误响应"""
        return ApiResponse.error(
            message=message,
            code=ResponseCode.SERVER_ERROR,
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    @staticmethod
    def paginated_success(data: list, total: int, page: int = 1, page_size: int = 10, 
                         message: str = "获取数据成功") -> JsonResponse:
        """分页成功响应"""
        paginated_data = {
            "list": data,
            "total": total,
            "page": page,
            "pageSize": page_size,
            "totalPage": (total + page_size - 1) // page_size
        }
        return ApiResponse.success(data=paginated_data, message=message)


class ResponseMixin:
    """响应Mixin，用于ViewSet"""
    
    def success_response(self, data: Any = None, message: str = "操作成功") -> JsonResponse:
        """成功响应"""
        return ApiResponse.success(data=data, message=message)
    
    def error_response(self, message: str = "操作失败", code: int = ResponseCode.ERROR) -> JsonResponse:
        """错误响应"""
        return ApiResponse.error(message=message, code=code)
    
    def unauthorized_response(self, message: str = "未登录或token已过期") -> JsonResponse:
        """未授权响应"""
        return ApiResponse.unauthorized(message=message)
    
    def forbidden_response(self, message: str = "权限不足") -> JsonResponse:
        """禁止访问响应"""
        return ApiResponse.forbidden(message=message)
    
    def not_found_response(self, message: str = "资源不存在") -> JsonResponse:
        """资源不存在响应"""
        return ApiResponse.not_found(message=message)
    
    def validation_error_response(self, message: str = "参数验证失败", errors: Dict = None) -> JsonResponse:
        """参数验证错误响应"""
        return ApiResponse.validation_error(message=message, errors=errors)

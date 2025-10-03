"""
RBAC工具模块
"""
from rest_framework.response import Response
from rest_framework import status


class ApiResponse:
    """统一API响应格式"""
    
    @staticmethod
    def success(data=None, message="操作成功", code=0):
        """成功响应"""
        return Response({
            'code': code,
            'message': message,
            'data': data,
            'success': True
        }, status=status.HTTP_200_OK)
    
    @staticmethod
    def error(message="操作失败", data=None, code=1):
        """错误响应"""
        return Response({
            'code': code,
            'message': message,
            'data': data,
            'success': False
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @staticmethod
    def not_found(message="资源不存在", code=404):
        """404响应"""
        return Response({
            'code': code,
            'message': message,
            'data': None,
            'success': False
        }, status=status.HTTP_404_NOT_FOUND)
    
    @staticmethod
    def unauthorized(message="未授权", code=401):
        """401响应"""
        return Response({
            'code': code,
            'message': message,
            'data': None,
            'success': False
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    @staticmethod
    def forbidden(message="禁止访问", code=403):
        """403响应"""
        return Response({
            'code': code,
            'message': message,
            'data': None,
            'success': False
        }, status=status.HTTP_403_FORBIDDEN)

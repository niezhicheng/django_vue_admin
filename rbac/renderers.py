"""
自定义响应渲染器
"""
from rest_framework.renderers import JSONRenderer
from rest_framework import status
from .response import ResponseCode


class ApiResponseRenderer(JSONRenderer):
    """统一API响应渲染器"""
    
    def render(self, data, accepted_media_type=None, renderer_context=None):
        """重写render方法，统一响应格式"""
        
        # 获取响应对象
        response = renderer_context.get('response') if renderer_context else None
        
        # 如果是错误响应且已经是规范格式，直接返回
        if data and isinstance(data, dict) and 'code' in data and 'success' in data:
            return super().render(data, accepted_media_type, renderer_context)
        
        # 统一包装响应数据
        if response:
            status_code = response.status_code
            
            # 成功响应
            if 200 <= status_code < 300:
                # 检查是否是分页数据
                if isinstance(data, dict) and 'results' in data and 'count' in data:
                    # 分页数据，保持原有结构
                    formatted_data = {
                        "code": ResponseCode.SUCCESS,
                        "message": "操作成功",
                        "data": data,
                        "success": True
                    }
                else:
                    # 普通数据
                    formatted_data = {
                        "code": ResponseCode.SUCCESS,
                        "message": "操作成功",
                        "data": data,
                        "success": True
                    }
            # 客户端错误
            elif 400 <= status_code < 500:
                message = "操作失败"
                code = ResponseCode.ERROR
                
                # 处理不同的错误类型
                if status_code == status.HTTP_401_UNAUTHORIZED:
                    message = "未登录或token已过期"
                    code = ResponseCode.UNAUTHORIZED
                elif status_code == status.HTTP_403_FORBIDDEN:
                    message = "权限不足"
                    code = ResponseCode.FORBIDDEN
                elif status_code == status.HTTP_404_NOT_FOUND:
                    message = "资源不存在"
                    code = ResponseCode.NOT_FOUND
                elif status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
                    message = "请求方法不允许"
                    code = ResponseCode.METHOD_NOT_ALLOWED
                elif status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
                    message = "参数验证失败"
                    code = ResponseCode.VALIDATION_ERROR
                
                # 如果data是错误详情，提取message
                if isinstance(data, dict):
                    if 'detail' in data:
                        message = data['detail']
                        data = None
                    elif 'non_field_errors' in data:
                        message = data['non_field_errors'][0] if data['non_field_errors'] else message
                        data = {"errors": data}
                    elif isinstance(data, dict) and len(data) == 1:
                        # 单个字段错误
                        field_name, field_errors = next(iter(data.items()))
                        if isinstance(field_errors, list) and field_errors:
                            message = f"{field_name}: {field_errors[0]}"
                        data = {"errors": data}
                    else:
                        data = {"errors": data}
                elif isinstance(data, str):
                    message = data
                    data = None
                
                formatted_data = {
                    "code": code,
                    "message": message,
                    "data": data,
                    "success": False
                }
            # 服务器错误
            else:
                formatted_data = {
                    "code": ResponseCode.SERVER_ERROR,
                    "message": "服务器内部错误",
                    "data": data if isinstance(data, dict) else None,
                    "success": False
                }
        else:
            # 默认成功响应
            formatted_data = {
                "code": ResponseCode.SUCCESS,
                "message": "操作成功",
                "data": data,
                "success": True
            }
        
        return super().render(formatted_data, accepted_media_type, renderer_context)

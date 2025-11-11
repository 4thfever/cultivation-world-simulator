"""Toast提示组件

用于显示临时的成功/失败/信息提示
"""
from typing import Optional


class Toast:
    """Toast提示
    
    显示短暂的提示信息，自动消失
    """
    
    # Toast类型
    SUCCESS = "success"
    ERROR = "error"
    INFO = "info"
    
    def __init__(self, pygame_mod):
        self.pygame = pygame_mod
        self.message: Optional[str] = None
        self.toast_type: str = Toast.INFO
        self.start_time: int = 0
        self.duration_ms: int = 3000  # 默认显示3秒
        self.is_visible: bool = False
    
    def show(self, message: str, toast_type: str = INFO, duration_ms: int = 3000):
        """显示Toast提示
        
        Args:
            message: 提示信息
            toast_type: 类型（success/error/info）
            duration_ms: 显示时长（毫秒）
        """
        self.message = message
        self.toast_type = toast_type
        self.duration_ms = duration_ms
        self.start_time = self.pygame.time.get_ticks()
        self.is_visible = True
    
    def update(self):
        """更新Toast状态，检查是否应该隐藏"""
        if not self.is_visible:
            return
        
        current_time = self.pygame.time.get_ticks()
        if current_time - self.start_time >= self.duration_ms:
            self.is_visible = False
            self.message = None
    
    def draw(self, screen, font):
        """绘制Toast
        
        Args:
            screen: pygame屏幕对象
            font: pygame字体对象
        """
        if not self.is_visible or not self.message:
            return
        
        pygame = self.pygame
        screen_w, screen_h = screen.get_size()
        
        # 根据类型选择颜色
        if self.toast_type == Toast.SUCCESS:
            bg_color = (34, 139, 34)  # 绿色
            border_color = (46, 184, 46)
        elif self.toast_type == Toast.ERROR:
            bg_color = (178, 34, 34)  # 红色
            border_color = (220, 50, 50)
        else:  # INFO
            bg_color = (70, 130, 180)  # 蓝色
            border_color = (100, 150, 200)
        
        # 计算淡入淡出效果
        elapsed = self.pygame.time.get_ticks() - self.start_time
        fade_in_duration = 200  # 淡入200ms
        fade_out_duration = 500  # 淡出500ms
        
        if elapsed < fade_in_duration:
            # 淡入阶段
            alpha = int(255 * (elapsed / fade_in_duration))
        elif elapsed > self.duration_ms - fade_out_duration:
            # 淡出阶段
            remaining = self.duration_ms - elapsed
            alpha = int(255 * (remaining / fade_out_duration))
        else:
            # 完全显示
            alpha = 255
        
        # 创建更大的字体用于Toast
        from .fonts import create_font
        toast_font = create_font(pygame, 24, None)  # 使用24号字体，更大更清晰
        
        # 处理多行文本
        lines = self.message.split('\n')
        text_surfaces = []
        max_text_w = 0
        total_text_h = 0
        line_spacing = 5  # 行间距
        
        for line in lines:
            text_surf = toast_font.render(line, True, (255, 255, 255))
            text_surfaces.append(text_surf)
            w, h = text_surf.get_size()
            max_text_w = max(max_text_w, w)
            total_text_h += h
        
        # 加上行间距
        total_text_h += line_spacing * (len(lines) - 1)
        
        # Toast尺寸（增大padding）
        padding_x = 40  # 水平padding增大
        padding_y = 25  # 垂直padding增大
        toast_w = max(max_text_w + padding_x * 2, 300)  # 最小宽度300
        toast_h = total_text_h + padding_y * 2
        
        # 位置：屏幕上方中央
        toast_x = (screen_w - toast_w) // 2
        toast_y = 100  # 稍微下移一点
        
        # 创建带透明度的surface
        toast_surface = pygame.Surface((toast_w, toast_h), pygame.SRCALPHA)
        
        # 绘制背景（带圆角和透明度）
        bg_with_alpha = (*bg_color, alpha)
        pygame.draw.rect(toast_surface, bg_with_alpha, (0, 0, toast_w, toast_h), border_radius=8)
        
        # 绘制边框
        border_with_alpha = (*border_color, alpha)
        pygame.draw.rect(toast_surface, border_with_alpha, (0, 0, toast_w, toast_h), 2, border_radius=8)
        
        # 绘制多行文本（应用透明度，居中显示）
        current_y = (toast_h - total_text_h) // 2  # 垂直居中起点
        for text_surf in text_surfaces:
            w, h = text_surf.get_size()
            text_with_alpha = pygame.Surface((w, h), pygame.SRCALPHA)
            text_with_alpha.blit(text_surf, (0, 0))
            text_with_alpha.set_alpha(alpha)
            text_x = (toast_w - w) // 2  # 每行水平居中
            toast_surface.blit(text_with_alpha, (text_x, current_y))
            current_y += h + line_spacing
        
        # 绘制到屏幕
        screen.blit(toast_surface, (toast_x, toast_y))


__all__ = ["Toast"]


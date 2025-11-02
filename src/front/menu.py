"""游戏暂停菜单"""
from typing import Optional, Tuple


class MenuOption:
    """菜单选项"""
    def __init__(self, label: str, action: str):
        self.label = label
        self.action = action


class PauseMenu:
    """暂停菜单"""
    def __init__(self, pygame_mod):
        self.pygame = pygame_mod
        self.is_visible = False
        self.options = [
            MenuOption("退出游戏", "quit")
        ]
        self.selected_index = 0
    
    def toggle(self):
        """切换菜单显示状态"""
        self.is_visible = not self.is_visible
        self.selected_index = 0
    
    def show(self):
        """显示菜单"""
        self.is_visible = True
    
    def hide(self):
        """隐藏菜单"""
        self.is_visible = False
    
    def handle_click(self, mouse_pos: Tuple[int, int], option_rects: list) -> Optional[str]:
        """处理鼠标点击，返回被点击的选项动作"""
        if not self.is_visible:
            return None
        
        for i, rect in enumerate(option_rects):
            if rect.collidepoint(mouse_pos):
                return self.options[i].action
        return None
    
    def draw(self, screen, colors, font):
        """绘制菜单"""
        if not self.is_visible:
            return []
        
        pygame = self.pygame
        screen_w, screen_h = screen.get_size()
        
        # 绘制半透明黑色背景（模糊效果）
        overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))
        
        # 计算菜单尺寸
        padding = 40
        option_height = 50
        option_spacing = 20
        menu_width = 300
        menu_height = padding * 2 + len(self.options) * option_height + (len(self.options) - 1) * option_spacing
        
        # 菜单居中位置
        menu_x = (screen_w - menu_width) // 2
        menu_y = (screen_h - menu_height) // 2
        
        # 绘制菜单背景
        menu_rect = pygame.Rect(menu_x, menu_y, menu_width, menu_height)
        pygame.draw.rect(screen, (40, 40, 40), menu_rect, border_radius=12)
        pygame.draw.rect(screen, (100, 100, 100), menu_rect, 2, border_radius=12)
        
        # 绘制选项
        option_rects = []
        current_y = menu_y + padding
        
        for i, option in enumerate(self.options):
            option_rect = pygame.Rect(
                menu_x + 30,
                current_y,
                menu_width - 60,
                option_height
            )
            
            # 检测鼠标悬停
            mouse_pos = pygame.mouse.get_pos()
            is_hovered = option_rect.collidepoint(mouse_pos)
            
            # 绘制选项背景
            bg_color = (80, 80, 80) if is_hovered else (50, 50, 50)
            pygame.draw.rect(screen, bg_color, option_rect, border_radius=8)
            pygame.draw.rect(screen, (120, 120, 120), option_rect, 1, border_radius=8)
            
            # 绘制选项文本
            text_color = (255, 255, 255) if is_hovered else (200, 200, 200)
            text_surf = font.render(option.label, True, text_color)
            text_x = option_rect.centerx - text_surf.get_width() // 2
            text_y = option_rect.centery - text_surf.get_height() // 2
            screen.blit(text_surf, (text_x, text_y))
            
            option_rects.append(option_rect)
            current_y += option_height + option_spacing
        
        return option_rects


__all__ = ["PauseMenu"]


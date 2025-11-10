import pandas as pd
import os
import glob
from utils.parser_factory import ParserFactory
import logging
import time

logger = logging.getLogger('FileProcessor')

class FileProcessor:
    """文件处理器"""
    
    @staticmethod
    def process_task(task_id, excel_path, txt_folder):
        """处理任务"""
        try:
            # 读取Excel文件
            df = pd.read_excel(excel_path)
            logger.info(f"读取Excel文件成功，共 {len(df)} 行数据")
            
            # 验证Excel结构
            FileProcessor._validate_excel_structure(df)
            
            # 处理每一行数据
            results = []
            total_rows = len(df)
            
            for index, row in df.iterrows():
                try:
                    channel = row['渠道']
                    txt_file = row['txt_file']
                    url = row.get('url', '')
                    
                    logger.info(f"处理第{index+1}行: 渠道={channel}, 文件={txt_file}")
                    
                    # 构建txt文件完整路径
                    txt_path = os.path.join(txt_folder, txt_file)
                    
                    if not os.path.exists(txt_path):
                        results.append({
                            **row.to_dict(),
                            '解析状态': 'error',
                            '解析结果': f'文件不存在: {txt_path}',
                            '解析详情': {}
                        })
                        continue
                    
                    # 创建解析器并解析
                    parser = ParserFactory.create_parser(channel, txt_path)
                    parse_result = parser.get_result()
                    
                    results.append({
                        **row.to_dict(),
                        '解析状态': parse_result.get('status', 'unknown'),
                        '解析结果': '解析成功' if parse_result.get('status') == 'success' else '解析失败',
                        '解析详情': parse_result
                    })
                    
                    # 更新进度
                    progress = int((index + 1) / total_rows * 100)
                    FileProcessor._update_task_progress(task_id, progress, f"已处理 {index + 1}/{total_rows}")
                    
                except Exception as e:
                    logger.error(f"处理第{index+1}行失败: {e}")
                    results.append({
                        **row.to_dict(),
                        '解析状态': 'error',
                        '解析结果': f'处理失败: {str(e)}',
                        '解析详情': {}
                    })
            
            # 保存结果
            result_file = FileProcessor._save_results(results, task_id)
            FileProcessor._update_task_progress(task_id, 100, "处理完成", status='completed', result_file=result_file)
            
            return result_file
            
        except Exception as e:
            logger.error(f"处理任务失败: {e}")
            FileProcessor._update_task_progress(task_id, 0, f"处理失败: {str(e)}", status='failed')
            raise
    
    @staticmethod
    def _validate_excel_structure(df):
        """验证Excel文件结构"""
        required_columns = ['渠道', 'url', 'txt_file']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Excel文件缺少必要列: {missing_columns}")
    
    @staticmethod
    def _save_results(results, task_id):
        """保存处理结果"""
        from models.task import Task
        
        result_df = pd.DataFrame(results)
        
        # 按渠道分sheet保存
        output_dir = os.path.dirname(Task.get_task(task_id).excel_file)
        output_path = os.path.join(output_dir, 'result.xlsx')
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # 获取所有渠道
            channels = result_df['渠道'].unique()
            
            # 为每个渠道创建sheet
            for channel in channels:
                # 过滤该渠道的数据
                channel_data = result_df[result_df['渠道'] == channel].copy()
                
                # 提取评论数据
                comments_data = FileProcessor._extract_comments_data(channel_data, channel)
                
                if not comments_data.empty:
                    # 清理sheet名称
                    sheet_name = FileProcessor._clean_sheet_name(channel)
                    
                    # 保存到sheet
                    comments_data.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # 添加汇总统计sheet
            summary_data = FileProcessor._create_summary_sheet(result_df)
            summary_data.to_excel(writer, sheet_name='汇总统计', index=False)
        
        return output_path
    
    @staticmethod
    def _extract_comments_data(channel_data, channel):
        """提取评论数据"""
        all_comments = []
        
        for index, row in channel_data.iterrows():
            if (row['解析状态'] == 'success' and 
                isinstance(row['解析详情'], dict) and 
                'comments' in row['解析详情']):
                
                comments = row['解析详情']['comments']
                for comment in comments:
                    # 根据渠道选择字段
                    comment_with_source = FileProcessor._format_comment_for_channel(comment, channel, row)
                    all_comments.append(comment_with_source)
        
        if all_comments:
            return pd.DataFrame(all_comments)
        else:
            return pd.DataFrame()
    
    @staticmethod
    def _format_comment_for_channel(comment, channel, row):
        """根据渠道格式化评论数据"""
        base_fields = {
            '来源文件': row['txt_file'],
            '来源URL': row.get('url', '')
        }
        
        # 根据不同渠道使用不同的字段映射
        if channel in ['抖音', '快手', '小红书', '微博']:
            formatted = {
                **base_fields,
                '作者': comment.get('作者', ''),
                '评论内容': comment.get('评论内容', ''),
                '评论时间': comment.get('评论时间', ''),
                '评论地点': comment.get('评论地点', ''),
                '图片地址': comment.get('图片地址', ''),
                '是否回复': comment.get('是否回复', '否'),
                '回复给': comment.get('回复给', '无')
            }
        elif channel == '今日头条':
            formatted = {
                **base_fields,
                '作者': comment.get('作者', ''),
                '评论内容': comment.get('评论内容', ''),
                '评论时间': comment.get('评论时间', ''),
                '点赞数': comment.get('点赞数', '0'),
                '评论地点': comment.get('评论地点', '未知地点')
            }
        else:
            formatted = {**base_fields, **comment}
        
        return formatted
    
    @staticmethod
    def _clean_sheet_name(sheet_name):
        """清理sheet名称"""
        import re
        cleaned = re.sub(r'[\\/*?\[\]:]', '', sheet_name)
        cleaned = cleaned[:31]  # 限制长度
        return cleaned
    
    @staticmethod
    def _create_summary_sheet(result_df):
        """创建汇总统计sheet"""
        summary_data = []
        
        # 按渠道统计
        for channel in result_df['渠道'].unique():
            channel_data = result_df[result_df['渠道'] == channel]
            total_count = len(channel_data)
            success_count = len(channel_data[channel_data['解析状态'] == 'success'])
            error_count = len(channel_data[channel_data['解析状态'] == 'error'])
            
            # 计算评论总数
            comments_count = 0
            for _, row in channel_data.iterrows():
                if (row['解析状态'] == 'success' and 
                    isinstance(row['解析详情'], dict) and 
                    'comments_count' in row['解析详情']):
                    comments_count += row['解析详情']['comments_count']
            
            summary_data.append({
                '渠道': channel,
                '处理文件数': total_count,
                '成功文件数': success_count,
                '失败文件数': error_count,
                '总评论数': comments_count,
                '成功率': f"{(success_count/total_count*100):.1f}%" if total_count > 0 else "0%"
            })
        
        # 总体统计
        total_stats = {
            '渠道': '总计',
            '处理文件数': len(result_df),
            '成功文件数': len(result_df[result_df['解析状态'] == 'success']),
            '失败文件数': len(result_df[result_df['解析状态'] == 'error']),
            '总评论数': '详见各渠道',
            '成功率': f"{(len(result_df[result_df['解析状态'] == 'success'])/len(result_df)*100):.1f}%" if len(result_df) > 0 else "0%"
        }
        
        summary_data.append(total_stats)
        return pd.DataFrame(summary_data)
    
    @staticmethod
    def _update_task_progress(task_id, progress, message, status='processing', result_file=None):
        """更新任务进度"""
        from models.task import Task
        
        task = Task.get_task(task_id)
        if task:
            task.update_progress(progress, message, status, result_file)
            
            # 添加延迟以显示进度效果
            if progress < 100 and status == 'processing':
                time.sleep(0.1)  # 100ms延迟，让进度条更平滑
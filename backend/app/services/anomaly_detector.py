# services/anomaly_detector.py
import numpy as np
import pandas as pd
from scipy import stats
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """异常数据检测服务"""
    
    @staticmethod
    def detect_outliers(
        data: List[Dict[str, Any]], 
        value_field: str = 'value',
        threshold: float = 3.0
    ) -> List[Dict[str, Any]]:
        """检测异常值（Z-score 方法）
        
        Args:
            data: 数据列表
            value_field: 值字段名
            threshold: Z-score 阈值，默认 3.0
        
        Returns:
            异常值列表
        """
        if len(data) < 3:
            logger.warning("数据量不足，无法检测异常值")
            return []
        
        # 提取数值
        values = []
        valid_indices = []
        for i, item in enumerate(data):
            value = item.get(value_field)
            if value is not None and isinstance(value, (int, float)):
                values.append(float(value))
                valid_indices.append(i)
        
        if len(values) < 3:
            logger.warning("有效数据量不足，无法检测异常值")
            return []
        
        # 计算 Z-score
        try:
            z_scores = np.abs(stats.zscore(values))
        except Exception as e:
            logger.error(f"计算 Z-score 失败: {e}")
            return []
        
        # 识别异常值
        outliers = []
        for idx, z_score in zip(valid_indices, z_scores):
            if z_score > threshold:
                anomaly = {
                    **data[idx],
                    'z_score': round(float(z_score), 2),
                    'anomaly_type': 'outlier',
                    'severity': 'high' if z_score > threshold * 1.5 else 'medium'
                }
                outliers.append(anomaly)
                logger.warning(f"检测到异常值: {data[idx].get('ts_code', 'unknown')} - "
                             f"{value_field}={data[idx].get(value_field)}, z_score={z_score:.2f}")
        
        logger.info(f"检测到 {len(outliers)} 个异常值")
        return outliers
    
    @staticmethod
    def detect_missing_data(
        data: List[Dict[str, Any]], 
        date_field: str = 'end_date',
        expected_interval_months: int = 3
    ) -> List[Dict[str, Any]]:
        """检测缺失的财报期
        
        Args:
            data: 数据列表（按日期降序排列）
            date_field: 日期字段名
            expected_interval_months: 预期间隔月数（默认 3 个月）
        
        Returns:
            缺失期间列表
        """
        if len(data) < 2:
            logger.warning("数据量不足，无法检测缺失期")
            return []
        
        # 提取日期并排序
        dates = []
        for item in data:
            date_str = item.get(date_field)
            if date_str:
                try:
                    if isinstance(date_str, str):
                        # 支持多种日期格式
                        if len(date_str) == 8:  # YYYYMMDD
                            date = datetime.strptime(date_str, '%Y%m%d')
                        else:  # YYYY-MM-DD
                            date = datetime.strptime(date_str.split('T')[0], '%Y-%m-%d')
                    elif isinstance(date_str, datetime):
                        date = date_str
                    else:
                        continue
                    dates.append((date, item.get('ts_code', 'unknown')))
                except Exception as e:
                    logger.warning(f"解析日期失败: {date_str}, {e}")
                    continue
        
        if len(dates) < 2:
            logger.warning("有效日期数据不足")
            return []
        
        # 按日期降序排序
        dates.sort(key=lambda x: x[0], reverse=True)
        
        # 检查间隔
        missing_periods = []
        expected_gap = timedelta(days=expected_interval_months * 30)
        
        for i in range(len(dates) - 1):
            current_date = dates[i][0]
            next_date = dates[i + 1][0]
            actual_gap = current_date - next_date
            
            # 如果实际间隔超过预期间隔的 1.5 倍，则认为有缺失
            if actual_gap > expected_gap * 1.5:
                missing_periods.append({
                    'ts_code': dates[i][1],
                    'from_date': next_date.strftime('%Y-%m-%d'),
                    'to_date': current_date.strftime('%Y-%m-%d'),
                    'expected_gap_months': expected_interval_months,
                    'actual_gap_months': round(actual_gap.days / 30, 1),
                    'anomaly_type': 'missing_data',
                    'severity': 'high' if actual_gap > expected_gap * 2 else 'medium'
                })
                logger.warning(f"检测到缺失期: {dates[i][1]} - "
                             f"从 {next_date.strftime('%Y-%m-%d')} 到 {current_date.strftime('%Y-%m-%d')}, "
                             f"实际间隔 {actual_gap.days} 天")
        
        logger.info(f"检测到 {len(missing_periods)} 个缺失期")
        return missing_periods
    
    @staticmethod
    def detect_negative_values(
        data: List[Dict[str, Any]], 
        fields: List[str],
        expected_positive: bool = True
    ) -> List[Dict[str, Any]]:
        """检测异常负值或正值
        
        Args:
            data: 数据列表
            fields: 需要检查的字段列表
            expected_positive: 期望为正值（True 检测异常负值，False 检测异常正值）
        
        Returns:
            异常值列表
        """
        anomalies = []
        
        for item in data:
            for field in fields:
                value = item.get(field)
                
                if value is None:
                    continue
                
                try:
                    value = float(value)
                except (TypeError, ValueError):
                    continue
                
                # 检查是否符合预期
                is_anomaly = False
                if expected_positive and value < 0:
                    is_anomaly = True
                    anomaly_desc = 'unexpected_negative'
                elif not expected_positive and value > 0:
                    is_anomaly = True
                    anomaly_desc = 'unexpected_positive'
                
                if is_anomaly:
                    anomaly = {
                        **item,
                        'field': field,
                        'value': value,
                        'anomaly_type': anomaly_desc,
                        'severity': 'medium'
                    }
                    anomalies.append(anomaly)
                    logger.warning(f"检测到异常值: {item.get('ts_code', 'unknown')} - "
                                 f"{field}={value} ({anomaly_desc})")
        
        logger.info(f"检测到 {len(anomalies)} 个异常符号值")
        return anomalies
    
    @staticmethod
    def detect_drastic_change(
        data: List[Dict[str, Any]],
        value_field: str = 'value',
        threshold_pct: float = 50.0
    ) -> List[Dict[str, Any]]:
        """检测剧烈变化（环比）
        
        Args:
            data: 数据列表（按日期排序）
            value_field: 值字段名
            threshold_pct: 变化百分比阈值
        
        Returns:
            剧烈变化列表
        """
        if len(data) < 2:
            logger.warning("数据量不足，无法检测变化")
            return []
        
        changes = []
        
        for i in range(1, len(data)):
            current_value = data[i].get(value_field)
            previous_value = data[i - 1].get(value_field)
            
            if current_value is None or previous_value is None:
                continue
            
            try:
                current_value = float(current_value)
                previous_value = float(previous_value)
            except (TypeError, ValueError):
                continue
            
            if previous_value == 0:
                continue
            
            change_pct = ((current_value - previous_value) / abs(previous_value)) * 100
            
            if abs(change_pct) > threshold_pct:
                change = {
                    **data[i],
                    'previous_value': previous_value,
                    'current_value': current_value,
                    'change_pct': round(change_pct, 2),
                    'anomaly_type': 'drastic_increase' if change_pct > 0 else 'drastic_decrease',
                    'severity': 'high' if abs(change_pct) > threshold_pct * 2 else 'medium'
                }
                changes.append(change)
                logger.warning(f"检测到剧烈变化: {data[i].get('ts_code', 'unknown')} - "
                             f"{value_field} 从 {previous_value} 变为 {current_value} "
                             f"({change_pct:+.2f}%)")
        
        logger.info(f"检测到 {len(changes)} 个剧烈变化")
        return changes
    
    @staticmethod
    def detect_all_anomalies(
        balance_sheets: List[Dict[str, Any]],
        income_statements: List[Dict[str, Any]],
        cash_flows: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """检测所有类型的异常
        
        Args:
            balance_sheets: 资产负债表数据
            income_statements: 利润表数据
            cash_flows: 现金流量表数据
        
        Returns:
            所有异常的字典
        """
        anomalies = {
            'outliers': [],
            'missing_periods': [],
            'negative_values': [],
            'drastic_changes': []
        }
        
        # 1. 检测资产负债表异常
        if balance_sheets:
            # 检测总资产异常值
            anomalies['outliers'].extend(
                AnomalyDetector.detect_outliers(balance_sheets, 'total_assets')
            )
            # 检测缺失期
            anomalies['missing_periods'].extend(
                AnomalyDetector.detect_missing_data(balance_sheets)
            )
            # 检测异常负值（总资产应该为正）
            anomalies['negative_values'].extend(
                AnomalyDetector.detect_negative_values(
                    balance_sheets, 
                    ['total_assets', 'total_equity', 'current_assets']
                )
            )
            # 检测剧烈变化
            anomalies['drastic_changes'].extend(
                AnomalyDetector.detect_drastic_change(balance_sheets, 'total_assets')
            )
        
        # 2. 检测利润表异常
        if income_statements:
            # 检测营业收入异常值
            anomalies['outliers'].extend(
                AnomalyDetector.detect_outliers(income_statements, 'revenue')
            )
            # 检测缺失期
            anomalies['missing_periods'].extend(
                AnomalyDetector.detect_missing_data(income_statements)
            )
            # 检测营业收入剧烈变化
            anomalies['drastic_changes'].extend(
                AnomalyDetector.detect_drastic_change(income_statements, 'revenue')
            )
        
        # 3. 检测现金流量表异常
        if cash_flows:
            # 检测经营现金流异常值
            anomalies['outliers'].extend(
                AnomalyDetector.detect_outliers(cash_flows, 'operating_cash_flow')
            )
            # 检测缺失期
            anomalies['missing_periods'].extend(
                AnomalyDetector.detect_missing_data(cash_flows)
            )
        
        # 统计总异常数
        total_anomalies = sum(len(v) for v in anomalies.values())
        logger.info(f"共检测到 {total_anomalies} 个异常")
        
        return anomalies
    
    @staticmethod
    def validate_data_quality(
        data: List[Dict[str, Any]],
        required_fields: List[str]
    ) -> Dict[str, Any]:
        """验证数据质量
        
        Args:
            data: 数据列表
            required_fields: 必需字段列表
        
        Returns:
            数据质量报告
        """
        if not data:
            return {
                'status': 'error',
                'message': '数据为空',
                'total_records': 0
            }
        
        total_records = len(data)
        missing_fields_count = {field: 0 for field in required_fields}
        null_values_count = {field: 0 for field in required_fields}
        
        for item in data:
            for field in required_fields:
                if field not in item:
                    missing_fields_count[field] += 1
                elif item[field] is None:
                    null_values_count[field] += 1
        
        # 计算完整性百分比
        completeness = {}
        for field in required_fields:
            missing = missing_fields_count[field] + null_values_count[field]
            completeness[field] = round((total_records - missing) / total_records * 100, 2)
        
        # 整体完整性
        overall_completeness = round(sum(completeness.values()) / len(required_fields), 2)
        
        report = {
            'status': 'ok' if overall_completeness >= 90 else 'warning',
            'total_records': total_records,
            'overall_completeness': overall_completeness,
            'field_completeness': completeness,
            'missing_fields': missing_fields_count,
            'null_values': null_values_count
        }
        
        logger.info(f"数据质量验证完成: 完整性 {overall_completeness}%")
        return report

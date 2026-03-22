-- 数据库迁移脚本
-- Week 4: 创建财务报表表结构
-- 版本: 001
-- 日期: 2026-03-22

-- ============================================
-- 1. 资产负债表 (balance_sheets)
-- ============================================
CREATE TABLE IF NOT EXISTS balance_sheets (
    id SERIAL PRIMARY KEY,
    ts_code VARCHAR(20) NOT NULL,
    end_date DATE NOT NULL,
    total_assets DECIMAL(20,2),
    total_liabilities DECIMAL(20,2),
    total_equity DECIMAL(20,2),
    current_assets DECIMAL(20,2),
    current_liabilities DECIMAL(20,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT balance_sheets_ts_code_end_date_unique UNIQUE (ts_code, end_date)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_balance_ts_code ON balance_sheets(ts_code);
CREATE INDEX IF NOT EXISTS idx_balance_end_date ON balance_sheets(end_date);
CREATE INDEX IF NOT EXISTS idx_balance_created_at ON balance_sheets(created_at);

-- 添加注释
COMMENT ON TABLE balance_sheets IS '资产负债表';
COMMENT ON COLUMN balance_sheets.ts_code IS '股票代码';
COMMENT ON COLUMN balance_sheets.end_date IS '报告期';
COMMENT ON COLUMN balance_sheets.total_assets IS '总资产';
COMMENT ON COLUMN balance_sheets.total_liabilities IS '总负债';
COMMENT ON COLUMN balance_sheets.total_equity IS '股东权益';
COMMENT ON COLUMN balance_sheets.current_assets IS '流动资产';
COMMENT ON COLUMN balance_sheets.current_liabilities IS '流动负债';

-- ============================================
-- 2. 利润表 (income_statements)
-- ============================================
CREATE TABLE IF NOT EXISTS income_statements (
    id SERIAL PRIMARY KEY,
    ts_code VARCHAR(20) NOT NULL,
    end_date DATE NOT NULL,
    revenue DECIMAL(20,2),
    net_profit DECIMAL(20,2),
    gross_profit DECIMAL(20,2),
    operating_profit DECIMAL(20,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT income_statements_ts_code_end_date_unique UNIQUE (ts_code, end_date)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_income_ts_code ON income_statements(ts_code);
CREATE INDEX IF NOT EXISTS idx_income_end_date ON income_statements(end_date);
CREATE INDEX IF NOT EXISTS idx_income_created_at ON income_statements(created_at);

-- 添加注释
COMMENT ON TABLE income_statements IS '利润表';
COMMENT ON COLUMN income_statements.ts_code IS '股票代码';
COMMENT ON COLUMN income_statements.end_date IS '报告期';
COMMENT ON COLUMN income_statements.revenue IS '营业收入';
COMMENT ON COLUMN income_statements.net_profit IS '净利润';
COMMENT ON COLUMN income_statements.gross_profit IS '毛利润';
COMMENT ON COLUMN income_statements.operating_profit IS '营业利润';

-- ============================================
-- 3. 现金流量表 (cash_flow_statements)
-- ============================================
CREATE TABLE IF NOT EXISTS cash_flow_statements (
    id SERIAL PRIMARY KEY,
    ts_code VARCHAR(20) NOT NULL,
    end_date DATE NOT NULL,
    operating_cash_flow DECIMAL(20,2),
    investing_cash_flow DECIMAL(20,2),
    financing_cash_flow DECIMAL(20,2),
    free_cash_flow DECIMAL(20,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT cash_flow_statements_ts_code_end_date_unique UNIQUE (ts_code, end_date)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_cashflow_ts_code ON cash_flow_statements(ts_code);
CREATE INDEX IF NOT EXISTS idx_cashflow_end_date ON cash_flow_statements(end_date);
CREATE INDEX IF NOT EXISTS idx_cashflow_created_at ON cash_flow_statements(created_at);

-- 添加注释
COMMENT ON TABLE cash_flow_statements IS '现金流量表';
COMMENT ON COLUMN cash_flow_statements.ts_code IS '股票代码';
COMMENT ON COLUMN cash_flow_statements.end_date IS '报告期';
COMMENT ON COLUMN cash_flow_statements.operating_cash_flow IS '经营活动现金流';
COMMENT ON COLUMN cash_flow_statements.investing_cash_flow IS '投资活动现金流';
COMMENT ON COLUMN cash_flow_statements.financing_cash_flow IS '筹资活动现金流';
COMMENT ON COLUMN cash_flow_statements.free_cash_flow IS '自由现金流';

-- ============================================
-- 4. 创建更新时间触发器
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为每个表添加触发器
DROP TRIGGER IF EXISTS update_balance_sheets_updated_at ON balance_sheets;
CREATE TRIGGER update_balance_sheets_updated_at
    BEFORE UPDATE ON balance_sheets
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_income_statements_updated_at ON income_statements;
CREATE TRIGGER update_income_statements_updated_at
    BEFORE UPDATE ON income_statements
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_cash_flow_statements_updated_at ON cash_flow_statements;
CREATE TRIGGER update_cash_flow_statements_updated_at
    BEFORE UPDATE ON cash_flow_statements
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 5. 创建视图：财务指标汇总
-- ============================================
CREATE OR REPLACE VIEW financial_metrics_summary AS
SELECT 
    b.ts_code,
    b.end_date,
    b.total_assets,
    b.total_liabilities,
    b.total_equity,
    b.current_assets,
    b.current_liabilities,
    i.revenue,
    i.net_profit,
    i.gross_profit,
    i.operating_profit,
    c.operating_cash_flow,
    c.investing_cash_flow,
    c.financing_cash_flow,
    c.free_cash_flow,
    -- 计算财务指标
    CASE WHEN b.total_equity > 0 THEN (i.net_profit / b.total_equity * 100) ELSE 0 END AS roe,
    CASE WHEN b.total_assets > 0 THEN (i.net_profit / b.total_assets * 100) ELSE 0 END AS roa,
    CASE WHEN b.total_assets > 0 THEN (b.total_liabilities / b.total_assets * 100) ELSE 0 END AS debt_ratio,
    CASE WHEN i.revenue > 0 THEN (i.gross_profit / i.revenue * 100) ELSE 0 END AS gross_margin,
    CASE WHEN b.current_liabilities > 0 THEN (b.current_assets / b.current_liabilities) ELSE 0 END AS current_ratio,
    CASE WHEN i.revenue > 0 THEN (i.operating_profit / i.revenue * 100) ELSE 0 END AS operating_margin,
    CASE WHEN i.revenue > 0 THEN (i.net_profit / i.revenue * 100) ELSE 0 END AS net_margin
FROM balance_sheets b
LEFT JOIN income_statements i ON b.ts_code = i.ts_code AND b.end_date = i.end_date
LEFT JOIN cash_flow_statements c ON b.ts_code = c.ts_code AND b.end_date = c.end_date
ORDER BY b.ts_code, b.end_date DESC;

COMMENT ON VIEW financial_metrics_summary IS '财务指标汇总视图';

-- ============================================
-- 完成
-- ============================================
-- 迁移完成提示
DO $$
BEGIN
    RAISE NOTICE '迁移 001_create_financial_tables 已完成';
END $$;

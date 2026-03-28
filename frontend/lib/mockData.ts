import {
  FinancialRecord,
  Market,
  ShareholderRecord,
  Stock
} from "@/lib/types";

/**
 * Mock datasets used when backend APIs are unavailable.
 */
export const mockData: {
  stocks: Stock[];
  financials: Record<string, FinancialRecord>;
  shareholders: Record<string, ShareholderRecord>;
} = {
  stocks: [
    {
      code: "600519",
      name: "贵州茅台",
      market: "A股",
      price: 1738.5,
      changePercent: 1.82,
      roe: 31.6,
      debtRatio: 18.2,
      pe: 28.4,
      reason: "品牌护城河稳固，现金流质量高，长期分红能力强。",
      tags: ["白酒龙头", "高ROE"]
    },
    {
      code: "000651",
      name: "格力电器",
      market: "A股",
      price: 42.18,
      changePercent: -0.63,
      roe: 22.1,
      debtRatio: 45.6,
      pe: 8.9,
      reason: "估值仍处低位，制造端效率稳定，股东回报政策明确。",
      tags: ["低估值", "高股息"]
    },
    {
      code: "600036",
      name: "招商银行",
      market: "A股",
      price: 34.76,
      changePercent: 0.47,
      roe: 16.4,
      debtRatio: 38.4,
      pe: 5.7,
      reason: "零售银行优势明显，资产质量稳健，拨备覆盖高。",
      tags: ["金融蓝筹", "稳健经营"]
    },
    {
      code: "AAPL",
      name: "Apple",
      market: "美股",
      price: 212.43,
      changePercent: 0.95,
      roe: 48.9,
      debtRatio: 28.2,
      pe: 31.6,
      reason: "生态系统粘性强，服务收入高质量增长，现金回购持续。",
      tags: ["品牌优势", "现金流强"]
    },
    {
      code: "MSFT",
      name: "Microsoft",
      market: "美股",
      price: 428.17,
      changePercent: 1.34,
      roe: 37.1,
      debtRatio: 30.1,
      pe: 33.2,
      reason: "云业务渗透率提升，企业软件续费率高，护城河深。",
      tags: ["云计算", "高壁垒"]
    },
    {
      code: "BRK.B",
      name: "Berkshire Hathaway",
      market: "美股",
      price: 468.32,
      changePercent: -0.21,
      roe: 17.3,
      debtRatio: 23.5,
      pe: 21.4,
      reason: "资本配置能力突出，保险浮存金构成长期优势。",
      tags: ["价值股", "多元资产"]
    },
    {
      code: "0700.HK",
      name: "腾讯控股",
      market: "港股",
      price: 388.6,
      changePercent: 2.14,
      roe: 19.2,
      debtRatio: 33.1,
      pe: 19.8,
      reason: "社交流量与游戏生态协同，回购节奏积极，盈利韧性较强。",
      tags: ["平台型公司", "回购"]
    },
    {
      code: "1810.HK",
      name: "小米集团",
      market: "港股",
      price: 18.54,
      changePercent: 3.27,
      roe: 15.8,
      debtRatio: 41.5,
      pe: 23.7,
      reason: "手机与生态链形成协同，汽车业务打开长期想象空间。",
      tags: ["成长股", "生态链"]
    },
    {
      code: "1299.HK",
      name: "友邦保险",
      market: "港股",
      price: 61.42,
      changePercent: -0.52,
      roe: 18.6,
      debtRatio: 24.8,
      pe: 14.3,
      reason: "寿险渠道能力强，区域布局分散，盈利稳定性较高。",
      tags: ["保险龙头", "现金创造"]
    },
    {
      code: "PDD",
      name: "拼多多",
      market: "美股",
      price: 147.9,
      changePercent: 1.76,
      roe: 27.4,
      debtRatio: 12.9,
      pe: 18.1,
      reason: "平台效率高，商家渗透深，利润释放速度快于预期。",
      tags: ["高增长", "平台经济"]
    }
  ],
  financials: {
    "600519": {
      code: "600519",
      company: "贵州茅台",
      metrics: [
        { label: "ROE", value: "31.6%", tone: "positive" },
        { label: "毛利率", value: "91.9%", tone: "positive" },
        { label: "负债率", value: "18.2%", tone: "positive" },
        { label: "PE", value: "28.4", tone: "neutral" },
        { label: "经营现金流", value: "812亿", tone: "positive" },
        { label: "净利润增长率", value: "15.2%", tone: "positive" }
      ],
      history: [
        { year: "2020", revenue: 979, netProfit: 466, roe: 29.5, grossMargin: 91.2, cashFlow: 540 },
        { year: "2021", revenue: 1062, netProfit: 524, roe: 30.1, grossMargin: 91.4, cashFlow: 602 },
        { year: "2022", revenue: 1241, netProfit: 627, roe: 31.3, grossMargin: 91.7, cashFlow: 688 },
        { year: "2023", revenue: 1477, netProfit: 747, roe: 32.0, grossMargin: 91.9, cashFlow: 752 },
        { year: "2024", revenue: 1588, netProfit: 820, roe: 31.6, grossMargin: 91.9, cashFlow: 812 }
      ],
      health: [
        { subject: "盈利", score: 95, fullMark: 100 },
        { subject: "成长", score: 82, fullMark: 100 },
        { subject: "偿债", score: 88, fullMark: 100 },
        { subject: "运营", score: 90, fullMark: 100 },
        { subject: "现金流", score: 94, fullMark: 100 },
        { subject: "估值", score: 72, fullMark: 100 }
      ]
    },
    AAPL: {
      code: "AAPL",
      company: "Apple",
      metrics: [
        { label: "ROE", value: "48.9%", tone: "positive" },
        { label: "毛利率", value: "45.6%", tone: "positive" },
        { label: "负债率", value: "28.2%", tone: "positive" },
        { label: "PE", value: "31.6", tone: "neutral" },
        { label: "经营现金流", value: "$118B", tone: "positive" },
        { label: "净利润增长率", value: "10.4%", tone: "positive" }
      ],
      history: [
        { year: "2020", revenue: 274, netProfit: 57, roe: 73.7, grossMargin: 38.2, cashFlow: 80 },
        { year: "2021", revenue: 365, netProfit: 95, roe: 147.4, grossMargin: 41.8, cashFlow: 104 },
        { year: "2022", revenue: 394, netProfit: 99, roe: 175.5, grossMargin: 43.3, cashFlow: 122 },
        { year: "2023", revenue: 383, netProfit: 97, roe: 156.1, grossMargin: 44.1, cashFlow: 111 },
        { year: "2024", revenue: 391, netProfit: 107, roe: 48.9, grossMargin: 45.6, cashFlow: 118 }
      ],
      health: [
        { subject: "盈利", score: 94, fullMark: 100 },
        { subject: "成长", score: 76, fullMark: 100 },
        { subject: "偿债", score: 86, fullMark: 100 },
        { subject: "运营", score: 91, fullMark: 100 },
        { subject: "现金流", score: 96, fullMark: 100 },
        { subject: "估值", score: 68, fullMark: 100 }
      ]
    },
    "0700.HK": {
      code: "0700.HK",
      company: "腾讯控股",
      metrics: [
        { label: "ROE", value: "19.2%", tone: "positive" },
        { label: "毛利率", value: "49.1%", tone: "positive" },
        { label: "负债率", value: "33.1%", tone: "positive" },
        { label: "PE", value: "19.8", tone: "positive" },
        { label: "经营现金流", value: "2410亿", tone: "positive" },
        { label: "净利润增长率", value: "22.5%", tone: "positive" }
      ],
      history: [
        { year: "2020", revenue: 4821, netProfit: 1598, roe: 20.3, grossMargin: 46.2, cashFlow: 1601 },
        { year: "2021", revenue: 5601, netProfit: 1882, roe: 18.8, grossMargin: 44.7, cashFlow: 1673 },
        { year: "2022", revenue: 5546, netProfit: 1156, roe: 9.7, grossMargin: 43.1, cashFlow: 1407 },
        { year: "2023", revenue: 6090, netProfit: 1577, roe: 15.4, grossMargin: 47.1, cashFlow: 2120 },
        { year: "2024", revenue: 6538, netProfit: 1934, roe: 19.2, grossMargin: 49.1, cashFlow: 2410 }
      ],
      health: [
        { subject: "盈利", score: 87, fullMark: 100 },
        { subject: "成长", score: 84, fullMark: 100 },
        { subject: "偿债", score: 79, fullMark: 100 },
        { subject: "运营", score: 83, fullMark: 100 },
        { subject: "现金流", score: 89, fullMark: 100 },
        { subject: "估值", score: 80, fullMark: 100 }
      ]
    }
  },
  shareholders: {
    "600519": {
      code: "600519",
      company: "贵州茅台",
      ownership: [
        { name: "机构投资者", value: 46 },
        { name: "国家持股", value: 39 },
        { name: "个人投资者", value: 15 }
      ],
      topHolders: [
        { rank: 1, name: "中国贵州茅台酒厂(集团)有限责任公司", shares: "6.83亿", ratio: "54.07%", change: "未变" },
        { rank: 2, name: "香港中央结算有限公司", shares: "1.06亿", ratio: "8.39%", change: "+0.12%" },
        { rank: 3, name: "中央汇金资产管理有限责任公司", shares: "1545万", ratio: "1.22%", change: "未变" },
        { rank: 4, name: "中国证券金融股份有限公司", shares: "1212万", ratio: "0.96%", change: "-0.02%" },
        { rank: 5, name: "全国社保基金一一八组合", shares: "970万", ratio: "0.77%", change: "+0.03%" }
      ],
      institutions: [
        { institution: "易方达蓝筹精选", position: "2310万股", ratio: "1.83%", action: "增持" },
        { institution: "景顺长城新兴成长", position: "1844万股", ratio: "1.46%", action: "持平" },
        { institution: "汇添富消费行业", position: "1192万股", ratio: "0.94%", action: "增持" }
      ]
    },
    AAPL: {
      code: "AAPL",
      company: "Apple",
      ownership: [
        { name: "共同基金", value: 42 },
        { name: "ETF", value: 23 },
        { name: "内部人", value: 1 },
        { name: "其他机构", value: 34 }
      ],
      topHolders: [
        { rank: 1, name: "Vanguard Group", shares: "1.39B", ratio: "8.6%", change: "+0.1%" },
        { rank: 2, name: "BlackRock", shares: "1.04B", ratio: "6.4%", change: "+0.2%" },
        { rank: 3, name: "Berkshire Hathaway", shares: "915M", ratio: "5.6%", change: "-0.1%" },
        { rank: 4, name: "State Street", shares: "586M", ratio: "3.6%", change: "持平" },
        { rank: 5, name: "FMR", shares: "332M", ratio: "2.0%", change: "+0.1%" }
      ],
      institutions: [
        { institution: "SPDR S&P 500 ETF", position: "183M", ratio: "1.13%", action: "增持" },
        { institution: "Invesco QQQ", position: "141M", ratio: "0.87%", action: "增持" },
        { institution: "T. Rowe Price", position: "89M", ratio: "0.55%", action: "减持" }
      ]
    },
    "0700.HK": {
      code: "0700.HK",
      company: "腾讯控股",
      ownership: [
        { name: "战略股东", value: 25 },
        { name: "机构投资者", value: 51 },
        { name: "个人投资者", value: 24 }
      ],
      topHolders: [
        { rank: 1, name: "Prosus", shares: "23.8亿", ratio: "25.59%", change: "-0.20%" },
        { rank: 2, name: "香港中央结算有限公司", shares: "8.6亿", ratio: "9.23%", change: "+0.14%" },
        { rank: 3, name: "贝莱德", shares: "3.1亿", ratio: "3.34%", change: "+0.04%" },
        { rank: 4, name: "富达基金", shares: "1.8亿", ratio: "1.95%", change: "持平" },
        { rank: 5, name: "摩根资产管理", shares: "1.4亿", ratio: "1.52%", change: "+0.02%" }
      ],
      institutions: [
        { institution: "南方东英恒生科技ETF", position: "6500万股", ratio: "0.70%", action: "增持" },
        { institution: "贝莱德中国基金", position: "4410万股", ratio: "0.47%", action: "持平" },
        { institution: "摩根亚洲基金", position: "3120万股", ratio: "0.34%", action: "增持" }
      ]
    }
  }
};

export const markets: Market[] = ["A股", "美股", "港股"];

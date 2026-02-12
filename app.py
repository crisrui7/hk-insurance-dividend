"""
香港保险分红实现率可视化平台 v2.0
Insurance Dividend Fulfillment Ratio Visualization Platform
"""

import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
import os

# 页面配置
st.set_page_config(
    page_title="香港保险分红实现率查询",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 样式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        padding-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_data():
    """加载数据"""
    db_path = os.path.join(os.path.dirname(__file__), 'insurance_data.db')
    conn = sqlite3.connect(db_path, check_same_thread=False)
    query = "SELECT * FROM product_fulfillment_rates"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def main():
    """主应用"""
    
    # 标题
    st.markdown('<div class="main-header">📊 香港保险分红实现率查询平台</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">一站式查询香港各大保险公司分红实现率数据</div>', unsafe_allow_html=True)
    
    # 加载数据
    with st.spinner('加载数据中...'):
        df = load_data()
    
    # 侧边栏筛选
    st.sidebar.header("🔍 筛选条件")
    
    # 公司筛选
    companies = ['全部'] + sorted(df['company'].unique().tolist())
    selected_company = st.sidebar.selectbox('保险公司', companies)
    
    # 根据公司筛选数据
    if selected_company != '全部':
        df_filtered = df[df['company'] == selected_company]
    else:
        df_filtered = df.copy()
    
    # 产品筛选
    products = ['全部'] + sorted(df_filtered['product_name'].unique().tolist())
    selected_product = st.sidebar.selectbox('产品名称', products)
    
    # 根据产品筛选
    if selected_product != '全部':
        df_filtered = df_filtered[df_filtered['product_name'] == selected_product]
    
    # 货币筛选
    currencies = ['全部'] + sorted(df_filtered['currency'].unique().tolist())
    selected_currency = st.sidebar.selectbox('货币', currencies)
    
    # 根据货币筛选
    if selected_currency != '全部':
        df_filtered = df_filtered[df_filtered['currency'] == selected_currency]
    
    # 购买年份筛选
    if 'purchase_year' in df_filtered.columns:
        purchase_years = sorted([y for y in df_filtered['purchase_year'].unique() if pd.notna(y)], reverse=True)
        if purchase_years:
            selected_years = st.sidebar.multiselect(
                '购买年份',
                purchase_years,
                default=purchase_years[:5] if len(purchase_years) >= 5 else purchase_years
            )
            
            if selected_years:
                df_filtered = df_filtered[df_filtered['purchase_year'].isin(selected_years)]
    
    # 关键指标
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📦 产品数量", f"{df_filtered['product_name'].nunique()}")
    
    with col2:
        # 计算平均归原红利实现率
        avg_rev = df_filtered['reversionary_bonus_rate'].dropna().mean()
        if pd.notna(avg_rev):
            st.metric("📈 平均归原红利实现率", f"{avg_rev:.1f}%")
        else:
            st.metric("📈 平均归原红利实现率", "N/A")
    
    with col3:
        # 计算平均特别红利实现率
        avg_spe = df_filtered['special_bonus_rate'].dropna().mean()
        if pd.notna(avg_spe):
            st.metric("🎯 平均特别红利实现率", f"{avg_spe:.1f}%")
        else:
            st.metric("🎯 平均特别红利实现率", "N/A")
    
    with col4:
        st.metric("📊 数据记录", f"{len(df_filtered)}")
    
    st.markdown("---")
    
    # 主要内容区域
    if len(df_filtered) == 0:
        st.warning("⚠️ 没有符合筛选条件的数据")
        return
    
    # 标签页
    tab1, tab2, tab3 = st.tabs(["📈 趋势图表", "📋 详细数据", "📊 对比分析"])
    
    with tab1:
        st.subheader("分红实现率趋势")
        
        # 准备图表数据
        chart_data = df_filtered.copy()
        
        if selected_product != '全部' and len(chart_data) > 0:
            # 单产品展示：按购买年份展示归原红利和特别红利
            fig = go.Figure()
            
            # 归原红利
            if chart_data['reversionary_bonus_rate'].notna().any():
                fig.add_trace(go.Scatter(
                    x=chart_data['purchase_year'],
                    y=chart_data['reversionary_bonus_rate'],
                    mode='lines+markers',
                    name='归原红利',
                    line=dict(color='#1f77b4', width=3),
                    marker=dict(size=10)
                ))
            
            # 特别红利
            if chart_data['special_bonus_rate'].notna().any():
                fig.add_trace(go.Scatter(
                    x=chart_data['purchase_year'],
                    y=chart_data['special_bonus_rate'],
                    mode='lines+markers',
                    name='特别红利',
                    line=dict(color='#ff7f0e', width=3),
                    marker=dict(size=10)
                ))
            
            # 周年红利
            if chart_data['annual_bonus_rate'].notna().any():
                fig.add_trace(go.Scatter(
                    x=chart_data['purchase_year'],
                    y=chart_data['annual_bonus_rate'],
                    mode='lines+markers',
                    name='周年红利',
                    line=dict(color='#2ca02c', width=3),
                    marker=dict(size=10)
                ))
            
            # 终期红利
            if chart_data['terminal_bonus_rate'].notna().any():
                fig.add_trace(go.Scatter(
                    x=chart_data['purchase_year'],
                    y=chart_data['terminal_bonus_rate'],
                    mode='lines+markers',
                    name='终期红利',
                    line=dict(color='#d62728', width=3),
                    marker=dict(size=10)
                ))
            
            # 100%基准线
            fig.add_hline(y=100, line_dash="dash", line_color="gray", 
                         annotation_text="100%基准", annotation_position="right")
            
            fig.update_layout(
                title=f"{selected_product} - 分红实现率趋势",
                xaxis_title="购买年份",
                yaxis_title="实现率 (%)",
                hovermode='x unified',
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        else:
            # 多产品展示：按产品对比平均实现率
            product_stats = []
            
            for product in chart_data['product_name'].unique():
                product_data = chart_data[chart_data['product_name'] == product]
                
                avg_rev = product_data['reversionary_bonus_rate'].dropna().mean()
                avg_spe = product_data['special_bonus_rate'].dropna().mean()
                avg_ann = product_data['annual_bonus_rate'].dropna().mean()
                
                product_stats.append({
                    '产品名称': product,
                    '归原红利': avg_rev if pd.notna(avg_rev) else None,
                    '特别红利': avg_spe if pd.notna(avg_spe) else None,
                    '周年红利': avg_ann if pd.notna(avg_ann) else None
                })
            
            stats_df = pd.DataFrame(product_stats)
            
            # 柱状图
            fig = go.Figure()
            
            if '归原红利' in stats_df.columns and stats_df['归原红利'].notna().any():
                fig.add_trace(go.Bar(
                    name='归原红利',
                    x=stats_df['产品名称'],
                    y=stats_df['归原红利'],
                    marker_color='#1f77b4'
                ))
            
            if '特别红利' in stats_df.columns and stats_df['特别红利'].notna().any():
                fig.add_trace(go.Bar(
                    name='特别红利',
                    x=stats_df['产品名称'],
                    y=stats_df['特别红利'],
                    marker_color='#ff7f0e'
                ))
            
            if '周年红利' in stats_df.columns and stats_df['周年红利'].notna().any():
                fig.add_trace(go.Bar(
                    name='周年红利',
                    x=stats_df['产品名称'],
                    y=stats_df['周年红利'],
                    marker_color='#2ca02c'
                ))
            
            fig.update_layout(
                title="各产品平均分红实现率对比",
                xaxis_title="产品名称",
                yaxis_title="平均实现率 (%)",
                barmode='group',
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("详细数据表")
        
        # 准备展示数据
        display_df = df_filtered[[
            'company', 'product_name', 'currency', 'purchase_year',
            'reversionary_bonus_rate', 'special_bonus_rate', 
            'annual_bonus_rate', 'terminal_bonus_rate', 'total_cash_value_rate'
        ]].copy()
        
        # 重命名列
        display_df.columns = [
            '保险公司', '产品名称', '货币', '购买年份',
            '归原红利(%)', '特别红利(%)', '周年红利(%)', '终期红利(%)', '总现金价值(%)'
        ]
        
        # 排序
        display_df = display_df.sort_values(['保险公司', '产品名称', '购买年份'], ascending=[True, True, False])
        
        # 显示数据
        st.dataframe(
            display_df,
            use_container_width=True,
            height=500
        )
        
        # 下载按钮
        csv = display_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 下载数据(CSV)",
            data=csv,
            file_name=f"dividend_fulfillment_rates_{selected_company}_{selected_product}.csv",
            mime="text/csv"
        )
    
    with tab3:
        st.subheader("产品对比分析")
        
        if selected_product == '全部':
            st.info("💡 请在侧边栏选择具体产品以查看详细对比分析")
        else:
            # 雷达图：对比不同购买年份的表现
            product_data = df_filtered[df_filtered['product_name'] == selected_product]
            
            if len(product_data) > 0:
                # 准备雷达图数据
                categories = []
                values_dict = {}
                
                for _, row in product_data.iterrows():
                    year = row['purchase_year']
                    if pd.notna(year):
                        year_label = f"{int(year)}年"
                        values = []
                        
                        if pd.notna(row['reversionary_bonus_rate']):
                            if '归原红利' not in categories:
                                categories.append('归原红利')
                        
                        if pd.notna(row['special_bonus_rate']):
                            if '特别红利' not in categories:
                                categories.append('特别红利')
                        
                        if pd.notna(row['annual_bonus_rate']):
                            if '周年红利' not in categories:
                                categories.append('周年红利')
                        
                        if pd.notna(row['terminal_bonus_rate']):
                            if '终期红利' not in categories:
                                categories.append('终期红利')
                
                # 创建雷达图
                if categories:
                    fig = go.Figure()
                    
                    for _, row in product_data.head(5).iterrows():  # 最多显示5个年份
                        year = row['purchase_year']
                        if pd.notna(year):
                            values = []
                            for cat in categories:
                                if cat == '归原红利':
                                    values.append(row['reversionary_bonus_rate'] if pd.notna(row['reversionary_bonus_rate']) else 0)
                                elif cat == '特别红利':
                                    values.append(row['special_bonus_rate'] if pd.notna(row['special_bonus_rate']) else 0)
                                elif cat == '周年红利':
                                    values.append(row['annual_bonus_rate'] if pd.notna(row['annual_bonus_rate']) else 0)
                                elif cat == '终期红利':
                                    values.append(row['terminal_bonus_rate'] if pd.notna(row['terminal_bonus_rate']) else 0)
                            
                            fig.add_trace(go.Scatterpolar(
                                r=values,
                                theta=categories,
                                fill='toself',
                                name=f"{int(year)}年购买"
                            ))
                    
                    fig.update_layout(
                        polar=dict(
                            radialaxis=dict(
                                visible=True,
                                range=[0, 120]
                            )
                        ),
                        showlegend=True,
                        title=f"{selected_product} - 不同购买年份对比",
                        height=500
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("该产品暂无可对比的数据")
            else:
                st.warning("暂无数据")
    
    # 页脚
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; font-size: 0.9rem;'>
        <p>数据来源：香港各大保险公司官方网站 | 最后更新：2024年</p>
        <p>⚠️ 本平台仅供参考，具体产品信息请以保险公司官方公布为准</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == '__main__':
    main()

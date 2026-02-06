"""
香港保险分红实现率可视化平台
Insurance Dividend Fulfillment Ratio Visualization Platform
"""

import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go

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
    .status-badge {
        padding: 0.2rem 0.5rem;
        border-radius: 0.3rem;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .status-normal { background-color: #90EE90; color: #006400; }
    .status-discontinued { background-color: #FFB6C1; color: #8B0000; }
    .status-pending { background-color: #FFE4B5; color: #8B4500; }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
   def load_data():
       """加载数据"""
       # 使用相对路径，兼容本地和云端部署
       import os
       db_path = os.path.join(os.path.dirname(__file__), 'insurance_data.db')
       conn = sqlite3.connect(db_path, check_same_thread=False)
       query = "SELECT * FROM fulfillment_ratios"
       df = pd.read_sql_query(query, conn)
       return df


def get_status_display(status):
    """状态显示转换"""
    status_map = {
        'normal': '正常',
        'discontinued': '已停售',
        'not_launched': '未推出',
        'no_dividend': '無分紅',
        'no_termination': '無保單終結',
        'not_reached_yet': '未達保單年期',
        'no_policy': '無保單'
    }
    return status_map.get(status, status)


def get_status_color(status):
    """状态颜色"""
    color_map = {
        'normal': '#90EE90',
        'discontinued': '#FFB6C1',
        'not_launched': '#FFE4B5',
        'no_dividend': '#FFE4B5',
        'no_termination': '#FFE4B5',
        'not_reached_yet': '#FFE4B5',
        'no_policy': '#FFB6C1'
    }
    return color_map.get(status, '#D3D3D3')


def main():
    """主应用"""
    
    # 标题
    st.markdown('<div class="main-header">📊 香港保险分红实现率查询平台</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">一站式查询香港各大保险公司分红实现率数据</div>', unsafe_allow_html=True)
    
    # 加载数据
    df = load_data()
    
    # 侧边栏 - 筛选器
    st.sidebar.header("🔍 筛选条件")
    
    # 公司选择
    companies = ['全部'] + sorted(df['company'].unique().tolist())
    selected_company = st.sidebar.selectbox("选择保险公司", companies)
    
    # 根据公司筛选产品
    if selected_company != '全部':
        filtered_df = df[df['company'] == selected_company]
    else:
        filtered_df = df
    
    # 产品选择
    products = ['全部'] + sorted(filtered_df['product_name'].unique().tolist())
    selected_product = st.sidebar.selectbox("选择产品", products)
    
    # 根据产品进一步筛选
    if selected_product != '全部':
        filtered_df = filtered_df[filtered_df['product_name'] == selected_product]
    
    # 货币选择
    currencies = ['全部'] + sorted(filtered_df['currency'].unique().tolist())
    selected_currency = st.sidebar.selectbox("选择货币", currencies)
    
    if selected_currency != '全部':
        filtered_df = filtered_df[filtered_df['currency'] == selected_currency]
    
    # 类别选择
    categories = ['全部'] + sorted(filtered_df['category'].unique().tolist())
    selected_category = st.sidebar.selectbox("选择类别", categories)
    
    if selected_category != '全部':
        filtered_df = filtered_df[filtered_df['category'] == selected_category]
    
    # 保单年期范围
    min_year = int(df['policy_year'].min())
    max_year = int(df['policy_year'].max())
    year_range = st.sidebar.slider(
        "保单年期范围",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year)
    )
    
    filtered_df = filtered_df[
        (filtered_df['policy_year'] >= year_range[0]) &
        (filtered_df['policy_year'] <= year_range[1])
    ]
    
    # 状态筛选
    show_all_status = st.sidebar.checkbox("显示所有状态（包括已停售、未推出等）", value=True)
    if not show_all_status:
        filtered_df = filtered_df[filtered_df['status'] == 'normal']
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📌 说明")
    st.sidebar.info("""
    **分红实现率**是指实际派发的分红与销售时承诺的分红之比。
    
    - **100%**: 完全实现承诺
    - **>100%**: 超额实现
    - **<100%**: 未完全实现
    """)
    
    # 主界面
    # 关键指标
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("产品数量", filtered_df['product_name'].nunique())
    
    with col2:
        normal_records = filtered_df[filtered_df['status'] == 'normal']
        if len(normal_records) > 0:
            avg_rate = normal_records['fulfillment_rate'].mean()
            st.metric("平均实现率", f"{avg_rate:.1f}%")
        else:
            st.metric("平均实现率", "N/A")
    
    with col3:
        st.metric("数据记录", len(filtered_df))
    
    with col4:
        st.metric("数据年度", df['data_year'].iloc[0])
    
    # 标签页
    tab1, tab2, tab3 = st.tabs(["📈 趋势图表", "📋 详细数据", "📊 对比分析"])
    
    with tab1:
        st.subheader("分红实现率趋势")
        
        # 只显示有实际数值的数据
        plot_df = filtered_df[filtered_df['status'] == 'normal'].copy()
        
        if len(plot_df) > 0:
            # 按产品和年期绘制折线图
            if selected_product != '全部':
                # 单产品详细视图
                fig = px.line(
                    plot_df,
                    x='policy_year',
                    y='fulfillment_rate',
                    color='category',
                    line_group='currency',
                    markers=True,
                    title=f"{selected_product} 分红实现率趋势",
                    labels={
                        'policy_year': '保单年期',
                        'fulfillment_rate': '分红实现率 (%)',
                        'category': '类别'
                    }
                )
            else:
                # 多产品对比视图
                fig = px.line(
                    plot_df,
                    x='policy_year',
                    y='fulfillment_rate',
                    color='product_name',
                    markers=True,
                    title="各产品分红实现率对比",
                    labels={
                        'policy_year': '保单年期',
                        'fulfillment_rate': '分红实现率 (%)',
                        'product_name': '产品名称'
                    }
                )
            
            fig.add_hline(y=100, line_dash="dash", line_color="red", 
                         annotation_text="100% 基准线")
            
            fig.update_layout(height=500, hovermode='x unified')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("当前筛选条件下没有可显示的趋势数据")
        
        # 柱状图 - 按年期分组
        if len(plot_df) > 0:
            st.subheader("各年期分红实现率分布")
            
            fig2 = px.bar(
                plot_df.groupby('policy_year')['fulfillment_rate'].mean().reset_index(),
                x='policy_year',
                y='fulfillment_rate',
                title="各保单年期平均分红实现率",
                labels={
                    'policy_year': '保单年期',
                    'fulfillment_rate': '平均分红实现率 (%)'
                }
            )
            
            fig2.add_hline(y=100, line_dash="dash", line_color="red")
            fig2.update_layout(height=400)
            st.plotly_chart(fig2, use_container_width=True)
    
    with tab2:
        st.subheader("详细数据表格")
        
        # 准备显示数据
        display_df = filtered_df.copy()
        display_df['状态显示'] = display_df['status'].apply(get_status_display)
        display_df['分红实现率'] = display_df.apply(
            lambda row: f"{row['fulfillment_rate']:.0f}%" 
            if pd.notna(row['fulfillment_rate']) else row['状态显示'],
            axis=1
        )
        
        # 选择显示列
        show_df = display_df[[
            'product_name', 'category', 'currency', 
            'policy_year', '分红实现率', 'status'
        ]].rename(columns={
            'product_name': '产品名称',
            'category': '类别',
            'currency': '货币',
            'policy_year': '保单年期',
            'status': '状态'
        })
        
        # 添加颜色标记函数
        def highlight_status(row):
            color = get_status_color(row['状态'])
            return [f'background-color: {color}' for _ in row]
        
        # 显示表格
        st.dataframe(
            show_df.style.apply(highlight_status, axis=1),
            use_container_width=True,
            height=600
        )
        
        # 下载按钮
        csv = filtered_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 下载数据 (CSV)",
            data=csv,
            file_name=f"分红实现率_{selected_product}_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    with tab3:
        st.subheader("产品对比分析")
        
        # 多产品选择器
        all_products = sorted(df['product_name'].unique().tolist())
        
        compare_products = st.multiselect(
            "选择要对比的产品（最多5个）",
            all_products,
            default=all_products[:min(3, len(all_products))],
            max_selections=5
        )
        
        if len(compare_products) >= 2:
            compare_df = df[df['product_name'].isin(compare_products)]
            compare_df = compare_df[compare_df['status'] == 'normal']
            
            # 雷达图
            if len(compare_df) > 0:
                fig3 = go.Figure()
                
                for product in compare_products:
                    product_data = compare_df[compare_df['product_name'] == product]
                    if len(product_data) > 0:
                        avg_by_year = product_data.groupby('policy_year')['fulfillment_rate'].mean()
                        
                        fig3.add_trace(go.Scatterpolar(
                            r=avg_by_year.values,
                            theta=[f"第{y}年" for y in avg_by_year.index],
                            name=product,
                            fill='toself'
                        ))
                
                fig3.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 120])),
                    title="产品分红实现率雷达图对比",
                    height=500
                )
                
                st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("请选择至少2个产品进行对比")
    
    # 页脚
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; font-size: 0.9rem;'>
        <p>数据来源：各保险公司官方网站 | 最后更新：2024年度报告</p>
        <p>⚠️ 过往表现不代表未来结果，投资需谨慎</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()

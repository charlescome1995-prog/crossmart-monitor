import re

with open('frontend/monitor.html', 'r', encoding='utf-8') as f:
    content = f.read()

old_start = '  rawData.items.forEach(item => {'
start_idx = content.find(old_start)
end_marker = "  tbody.innerHTML = html || '<tr><td colspan=\"7\" style=\"text-align:center; padding:40px 0; color:#999;\">未监测到任何匹配数据</td></tr>';"
end_idx = content.find(end_marker) + len(end_marker)
print(f'start={start_idx}, end={end_idx}, found={start_idx > 0}')

new_rendering = """  rawData.items.forEach(item => {
    const isStatusAnomaly = item.listing_status !== item.expected_listing_status;
    const isCatAnomaly = (item.main_cat !== item.expected_main_cat) || (item.sub_cat !== item.expected_sub_cat);
    const isInfoAnomaly = item.title_changed || item.img_changed || item.bullets_changed || item.description_changed;
    const isVariantAnomaly = item.variant_changed;
    const isPrimeAnomaly = item.prime_discount === '异常取消';
    const hasActiveAnomaly = item.chg !== 0 || isStatusAnomaly || isCatAnomaly || isInfoAnomaly || isVariantAnomaly || isPrimeAnomaly || (item.badges_lost.length > 0);

    if (sourceFilter !== 'ALL' && item.monitor_type !== sourceFilter) return;
    const matchesSearch = item.asin.toLowerCase().includes(searchTxt) || item.title.toLowerCase().includes(searchTxt) || item.brand.toLowerCase().includes(searchTxt);
    if (!matchesSearch) return;
    if (onlyChg && !hasActiveAnomaly) return;

    let activeEvents = [...item.events];
    if (isStatusAnomaly) activeEvents.push({ class: "e-alert", text: "状态异动: 变为" + item.listing_status });
    if (item.title_changed) activeEvents.push({ class: "e-alert", text: "标题发生变更" });
    if (item.img_changed) activeEvents.push({ class: "e-alert", text: "主图发生变更" });
    if (item.bullets_changed) activeEvents.push({ class: "e-alert", text: "五点描述遭篡改" });
    if (item.description_changed) activeEvents.push({ class: "e-alert", text: "产品描述遭篡改" });
    if (isCatAnomaly) activeEvents.push({ class: "e-alert", text: "类目遭异常篡改" });
    if (isVariantAnomaly) activeEvents.push({ class: "e-alert", text: "变体异动: " + item.variant_status });
    if (isPrimeAnomaly) activeEvents.push({ class: "e-alert", text: "Prime折扣异常取消" });
    item.badges_lost.forEach(badge => { activeEvents.push({ class: "e-alert", text: "失去 " + badge + " 标识" }); });
    if (item.deal_activity !== "无" && !isStatusAnomaly) activeEvents.push({ class: "e-promo", text: "活动: " + item.deal_activity });

    const chgClass = item.chg > 0 ? 'up' : (item.chg < 0 ? 'dn' : '');
    const chgText = item.chg > 0 ? "↑ $" + item.chg : (item.chg < 0 ? "↓ $" + Math.abs(item.chg) : '');

    const sourceHtml = "<span class=\"badge source-asin\">ASIN Stream</span>";
    let badgesHtml = '';
    item.badges_current.forEach(b => {
      let cls = b.toLowerCase() === 'a+' ? 'aplus' : (b.toLowerCase() === 'bs' ? 'bs' : (b.toLowerCase() === 'ac' ? 'ac' : 'nr'));
      badgesHtml += "<span class=\"badge-tag " + cls + "\">" + b + "</span>";
    });
    item.badges_lost.forEach(b => { badgesHtml += "<span class=\"badge-tag lost\" title=\"失去此标识\">" + b + "</span>"; });

    const statusTextHtml = item.listing_status === '正常' ? "<span style=\"color:#16a34a; font-weight:700;\">[状态: 正常]</span>" : "<span style=\"color:#dc2626; font-weight:700; background:#fef2f2; padding:1px 4px; border-radius:3px;\">[状态: " + item.listing_status + "]</span>";

    let eventsHtml = '<span class="e-none">指标平稳无告警</span>';
    if (activeEvents.length > 0) eventsHtml = activeEvents.map(e => "<span class=\"e-tag " + e.class + "\">" + e.text + "</span>").join('');

    const statusHtml = hasActiveAnomaly ? "<div class=\"status-indicator changed\">发现异动</div>" : "<div class=\"status-indicator stable\">稳定</div>";

    html += "<tr> \\
      <td class=\"col-img\"><img src=\"" + item.img + "\" alt=\"Product Picture\"></td> \\
      <td> \\
        <div class=\"info-block\"> \\
          <div>" + sourceHtml + " <span class=\"badge " + (item.is_main ? 'main' : 'rel') + "\">" + item.logic_type + "</span> " + statusTextHtml + "</div> \\
          <div><a href=\"https://www.amazon.com/dp/" + item.asin + "\" target=\"_blank\" class=\"asin-link\">" + item.asin + "</a> <span style=\"font-weight:700; color:#475569;\">[" + item.brand + "]</span></div> \\
          <div class=\"title-text\" title=\"" + item.title + "\">" + item.title + "</div> \\
          <div style=\"margin-top:2px;\">" + badgesHtml + "</div> \\
          <div style=\"color:#64748b; font-size:11px;\">变体状态: <strong style=\"color:#334155;\">" + item.variant_status + "</strong></div> \\
        </div> \\
      </td> \\
      <td> \\
        <div class=\"metrics-block\"> \\
          <div>价格走势: <strong style=\"font-size:13px;\">$" + item.price.toFixed(2) + "</strong> <span class=\"chg " + chgClass + "\">" + chgText + "</span></div> \\
          <div>优惠券流: <span style=\"background:#f0fdf4; color:#16a34a; padding:1px 4px; border-radius:3px; font-weight:700;\">" + item.coupon + "</span></div> \\
          <div>Prime折扣: <span style=\"background:#eff6ff; color:#2563eb; padding:1px 4px; border-radius:3px; font-weight:700;\">" + item.prime_discount + "</span></div> \\
          <div>营销活动: <span style=\"color:#ca8a04; font-weight:700;\">" + item.deal_activity + "</span></div> \\
          <div>买家反馈: <span style=\"color:#eab308;\">★</span> <strong>" + item.rating + "</strong> (" + item.reviews.toLocaleString() + ")</div> \\
          <div>大类节点: <span class=\"cat-item " + (item.main_cat !== item.expected_main_cat ? 'err' : '') + "\" title=\"当前: " + item.main_cat + " / 预期: " + item.expected_main_cat + "\">" + item.main_cat + "</span> <strong>#" + item.main_bsr.toLocaleString() + "</strong></div> \\
          <div>小类节点: <span class=\"cat-item " + (item.sub_cat !== item.expected_sub_cat ? 'err' : '') + "\" title=\"当前: " + item.sub_cat + " / 预期: " + item.expected_sub_cat + "\">" + item.sub_cat + "</span> <strong>#" + item.sub_bsr.toLocaleString() + "</strong></div> \\
        </div> \\
      </td> \\
      <td><div class=\"events-cell\">" + eventsHtml + "</div></td> \\
      <td> \\
        <div class=\"trend-container\"> \\
          <div class=\"trend-label\">大类排名曲线 (Main BSR)</div> \\
          " + drawSparkline(item.history_main_bsr, '#1e3a8a') + " \\
          <div class=\"trend-label\" style=\"margin-top:2px;\">小类排名曲线 (Sub BSR)</div> \\
          " + drawSparkline(item.history_sub_bsr, '#0d9488') + " \\
        </div> \\
      </td> \\
      <td>" + statusHtml + "</td> \\
      <td style=\"color:#64748b; font-weight:700; font-size:12px;\">" + rawData.updated + "</td> \\
    </tr>";

    // related ASIN sub-rows
    if (item.related_asins && item.related_asins.length > 0) {
      item.related_asins.forEach(rel => {
        const relTypeLabel = rel.source || '竞品';
        html += "<tr style=\"background:#f8fafc;\"> \\
          <td class=\"col-img\"><div style=\"width:65px;height:85px;background:#e2e8f0;border-radius:4px;display:flex;align-items:center;justify-content:center;font-size:10px;color:#94a3b8;text-align:center;padding:4px;\">关联ASIN<br>无图片</div></td> \\
          <td> \\
            <div class=\"info-block\"> \\
              <div><span class=\"badge rel\">竞品 ASIN</span> <span style=\"font-size:10px;padding:1px 5px;background:#fce7f3;color:#db2777;border-radius:3px;font-weight:700;\">" + relTypeLabel + "</span></div> \\
              <div><a href=\"https://www.amazon.com/dp/" + rel.asin + "\" target=\"_blank\" class=\"asin-link\">" + rel.asin + "</a>" + (rel.brand ? "<span style=\"font-weight:700;color:#475569;\">[" + rel.brand + "]</span>" : "") + "</div> \\
              <div class=\"title-text\" title=\"" + (rel.title||'') + "\">" + (rel.title||'—') + "</div> \\
            </div> \\
          </td> \\
          <td> \\
            <div class=\"metrics-block\"> \\
              <div>价格: <strong>" + (rel.price||'—') + "</strong></div> \\
              <div>评分: <strong>" + (rel.rating||'—') + "</strong> " + (rel.reviews ? "(" + rel.reviews + ")" : "") + "</div> \\
              <div>BSR: <span style=\"color:#64748b;font-size:12px;\">" + ((rel.bsr||'').split('\\n')[0]||'—') + "</span></div> \\
            </div> \\
          </td> \\
          <td><span class=\"e-none\">竞品参考</span></td> \\
          <td><span style=\"color:#999;font-size:11px;\">—</span></td> \\
          <td><span style=\"color:#999;font-size:11px;\">—</span></td> \\
          <td style=\"color:#64748b;font-size:11px;\">" + rawData.updated + "</td> \\
        </tr>";
      });
    }
  });

  // keyword Top5 rows
  if (rawData.keywords && rawData.keywords.length > 0) {
    rawData.keywords.forEach(kw => {
      if (!kw.top_asins || kw.top_asins.length === 0) return;
      if (sourceFilter !== 'ALL' && sourceFilter !== 'KW') return;
      const kwMatch = kw.keyword.toLowerCase().includes(searchTxt);
      const asinsMatch = kw.top_asins.some(a => a.asin.toLowerCase().includes(searchTxt) || (a.title||'').toLowerCase().includes(searchTxt));
      if (searchTxt && !kwMatch && !asinsMatch) return;

      kw.top_asins.forEach((ta, idx) => {
        const typeLabel = ta.type || ta.rank || ("第" + (idx+1));
        const typeColor = ta.type === 'natural' ? '#16a34a' : (ta.type === 'ad' ? '#dc2626' : '#7c3aed');
        html += "<tr style=\"background:#fefce8;\"> \\
          <td class=\"col-img\"><div style=\"width:65px;height:85px;background:#fef3c7;border-radius:4px;display:flex;align-items:center;justify-content:center;font-size:10px;color:#ca8a04;text-align:center;padding:4px;\">关键词<br>竞争品</div></td> \\
          <td> \\
            <div class=\"info-block\"> \\
              <div><span class=\"badge source-kw\">Keyword Stream</span> <span style=\"font-size:10px;padding:1px 5px;background:#fef3c7;color:#ca8a04;border-radius:3px;font-weight:700;\">" + typeLabel + "</span></div> \\
              <div><a href=\"https://www.amazon.com/dp/" + ta.asin + "\" target=\"_blank\" class=\"asin-link\">" + ta.asin + "</a> <span style=\"color:#64748b;font-size:11px;\">[关键词: " + kw.keyword + "]</span></div> \\
              <div class=\"title-text\" title=\"" + (ta.title||'') + "\">" + (ta.title||'—') + "</div> \\
            </div> \\
          </td> \\
          <td> \\
            <div class=\"metrics-block\"> \\
              <div>价格: <strong>" + (ta.price||'—') + "</strong></div> \\
              <div>评分: <strong>" + ((ta.rating||'—').replace(' out of 5 stars','')) + "</strong> " + (ta.reviews ? "(" + ta.reviews + ")" : "") + "</div> \\
              <div>类型: <span style=\"font-weight:700;color:" + typeColor + "\">" + typeLabel + "</span></div> \\
            </div> \\
          </td> \\
          <td><span class=\"e-none\">关键词竞争品</span></td> \\
          <td><span style=\"color:#999;font-size:11px;\">—</span></td> \\
          <td><span style=\"color:#999;font-size:11px;\">—</span></td> \\
          <td style=\"color:#64748b;font-size:11px;\">" + rawData.updated + "</td> \\
        </tr>";
      });
    });
  }

  tbody.innerHTML = html || '<tr><td colspan="7" style="text-align:center; padding:40px 0; color:#999;">未监测到任何匹配数据</td></tr>';"""

new_content = content[:start_idx] + new_rendering + content[end_idx:]
with open('frontend/monitor.html', 'w', encoding='utf-8') as f:
    f.write(new_content)
print('Done! Wrote', len(new_content), 'chars')
# 基准测试结果

## 数据集统计

<table>
  <thead>
    <tr><th>数据集</th><th>规模</th><th>字段数</th><th>语言</th><th>用途</th></tr>
  </thead>
  <tbody>
    <tr><td align="left">SynthResume</td><td align="center">2,994</td><td align="center">15</td><td align="left">中文</td><td align="left">主要评测</td></tr>
    <tr><td align="left">RealResume</td><td align="center">13,100</td><td align="center">19</td><td align="left">中英混合</td><td align="left">主要评测 / 工业评测</td></tr>
    <tr><td align="left">ResumeBench</td><td align="center">2,500</td><td align="center">19</td><td align="left">5 种语言</td><td align="left">多语言泛化</td></tr>
  </tbody>
</table>

## 整体抽取性能

<table>
  <thead>
    <tr><th rowspan="2">类别</th><th rowspan="2">模型</th><th colspan="5">SynthResume 数据集</th><th colspan="5">RealResume 数据集</th></tr>
    <tr><th>宏平均准确率 ↑</th><th>宏平均精确率 ↑</th><th>宏平均召回率 ↑</th><th>宏平均 F1 ↑</th><th>耗时（秒）↓</th><th>宏平均准确率 ↑</th><th>宏平均精确率 ↑</th><th>宏平均召回率 ↑</th><th>宏平均 F1 ↑</th><th>耗时（秒）↓</th></tr>
  </thead>
  <tbody>
    <tr><td rowspan="2" align="center">Non-LLM baselines</td><td>BelloNLP</td><td align="center">0.8152</td><td align="center">0.7866</td><td align="center">0.7409</td><td align="center">0.7622</td><td align="center">1.43</td><td align="center">0.8812</td><td align="center">0.8481</td><td align="center">0.7802</td><td align="center">0.8106</td><td align="center">1.62</td></tr>
    <tr><td>PaddleNLP</td><td align="center">0.5763</td><td align="center">0.6693</td><td align="center">0.4741</td><td align="center">0.5231</td><td align="center">22.00</td><td align="center">0.5146</td><td align="center">0.5838</td><td align="center">0.4220</td><td align="center">0.4595</td><td align="center">20.90</td></tr>
    <tr><td rowspan="5" align="center">OCR-only LLMs</td><td>Claude-opus-5-5</td><td align="center">0.9293</td><td align="center">0.9289</td><td align="center">0.9236</td><td align="center">0.9254</td><td align="center">10.709</td><td align="center">0.9245</td><td align="center">0.8771</td><td align="center">0.9343</td><td align="center">0.8995</td><td align="center">21.982</td></tr>
    <tr><td>Gemini-3.8-flash</td><td align="center">0.9338</td><td align="center">0.9397</td><td align="center">0.9297</td><td align="center">0.9341</td><td align="center">22.320</td><td align="center">0.9426</td><td align="center">0.9327</td><td align="center">0.9497</td><td align="center">0.9397</td><td align="center">33.736</td></tr>
    <tr><td>GPT-6.1-sol</td><td align="center">0.9208</td><td align="center">0.9194</td><td align="center">0.9111</td><td align="center">0.9141</td><td align="center">8.967</td><td align="center">0.9206</td><td align="center">0.8997</td><td align="center">0.9130</td><td align="center">0.9041</td><td align="center">18.075</td></tr>
    <tr><td>Qwen3.8-max</td><td align="center">0.9251</td><td align="center">0.9189</td><td align="center">0.9188</td><td align="center">0.9183</td><td align="center">6.129</td><td align="center">0.9426</td><td align="center">0.9287</td><td align="center">0.9395</td><td align="center">0.9333</td><td align="center">15.059</td></tr>
    <tr><td>Deepseek-v4-pro</td><td align="center">0.9445</td><td align="center"><ins>0.9520</ins></td><td align="center">0.9327</td><td align="center">0.9414</td><td align="center">3.485</td><td align="center">0.9536</td><td align="center">0.9328</td><td align="center">0.9425</td><td align="center">0.9370</td><td align="center">7.310</td></tr>
    <tr><td rowspan="8" align="center">Our Pipeline<br>(Zero-Shot LLM)</td><td>Claude-opus-5-5</td><td align="center">0.9410</td><td align="center">0.9392</td><td align="center">0.9329</td><td align="center">0.9356</td><td align="center">7.315</td><td align="center">0.9529</td><td align="center"><strong>0.9486</strong></td><td align="center">0.9619</td><td align="center"><strong>0.9539</strong></td><td align="center">17.140</td></tr>
    <tr><td>Gemini-3.8-flash</td><td align="center"><ins>0.9463</ins></td><td align="center">0.9461</td><td align="center"><ins>0.9390</ins></td><td align="center"><ins>0.9421</ins></td><td align="center">17.293</td><td align="center"><ins>0.9592</ins></td><td align="center">0.9435</td><td align="center">0.9589</td><td align="center"><ins>0.9506</ins></td><td align="center">20.633</td></tr>
    <tr><td>GPT-6.1-sol</td><td align="center">0.9323</td><td align="center">0.9267</td><td align="center">0.9219</td><td align="center">0.9236</td><td align="center">6.144</td><td align="center">0.9581</td><td align="center">0.9321</td><td align="center">0.9508</td><td align="center">0.9404</td><td align="center">13.185</td></tr>
    <tr><td>Deepseek-v4-pro</td><td align="center"><strong>0.9547</strong></td><td align="center"><strong>0.9525</strong></td><td align="center"><strong>0.9432</strong></td><td align="center"><strong>0.9473</strong></td><td align="center">3.326</td><td align="center">0.9566</td><td align="center"><ins>0.9445</ins></td><td align="center"><strong>0.9661</strong></td><td align="center"><strong>0.9539</strong></td><td align="center">6.535</td></tr>
    <tr><td>Qwen3.8-max</td><td align="center">0.9375</td><td align="center">0.9331</td><td align="center">0.9315</td><td align="center">0.9316</td><td align="center">5.318</td><td align="center">0.9542</td><td align="center">0.9369</td><td align="center">0.9533</td><td align="center">0.9441</td><td align="center">11.746</td></tr>
    <tr><td>Qwen3-14B</td><td align="center">0.9111</td><td align="center">0.9059</td><td align="center">0.9107</td><td align="center">0.9081</td><td align="center">6.30</td><td align="center">0.9266</td><td align="center">0.8977</td><td align="center">0.9258</td><td align="center">0.9098</td><td align="center">8.55</td></tr>
    <tr><td>Qwen3-4B</td><td align="center">0.8852</td><td align="center">0.876</td><td align="center">0.895</td><td align="center">0.885</td><td align="center">5.24</td><td align="center">0.8967</td><td align="center">0.8604</td><td align="center">0.9124</td><td align="center">0.8830</td><td align="center">6.85</td></tr>
    <tr><td>Qwen3-0.6B</td><td align="center">0.6176</td><td align="center">0.6705</td><td align="center">0.6633</td><td align="center">0.6448</td><td align="center">1.22</td><td align="center">0.6286</td><td align="center">0.6722</td><td align="center">0.6673</td><td align="center">0.6575</td><td align="center">1.54</td></tr>
    <tr><td rowspan="1" align="center">Our Pipeline<br>(Fine-Tuned LLM)</td><td>Qwen3-0.6B-SFT</td><td align="center">0.9314</td><td align="center">0.9177</td><td align="center">0.9173</td><td align="center">0.9172</td><td align="center">1.22</td><td align="center"><strong>0.9613</strong></td><td align="center">0.9383</td><td align="center"><ins>0.9648</ins></td><td align="center">0.9501</td><td align="center">1.54</td></tr>
  </tbody>
</table>



## SynthResume 细分字段性能


<table>
  <thead>
    <tr><th rowspan="2">模型</th><th colspan="4">时间字段</th><th colspan="4">命名实体</th><th colspan="4">长文本</th></tr>
    <tr><th>宏平均准确率</th><th>宏平均精确率</th><th>宏平均召回率</th><th>宏平均 F1</th><th>宏平均准确率</th><th>宏平均精确率</th><th>宏平均召回率</th><th>宏平均 F1</th><th>宏平均准确率</th><th>宏平均精确率</th><th>宏平均召回率</th><th>宏平均 F1</th></tr>
  </thead>
  <tbody>
    <tr><td colspan="13"><em>Non-LLM baselines</em></td></tr>
    <tr><td>Bello</td><td align="center">0.852</td><td align="center">0.922</td><td align="center">0.852</td><td align="center">0.885</td><td align="center">0.841</td><td align="center">0.781</td><td align="center">0.720</td><td align="center">0.749</td><td align="center">0.469</td><td align="center">0.246</td><td align="center">0.273</td><td align="center">0.259</td></tr>
    <tr><td>PaddleNLP</td><td align="center">0.433</td><td align="center">0.723</td><td align="center">0.407</td><td align="center">0.511</td><td align="center">0.818</td><td align="center">0.727</td><td align="center">0.679</td><td align="center">0.699</td><td align="center">0.272</td><td align="center">-</td><td align="center">-</td><td align="center">-</td></tr>
    <tr><td colspan="13"><em>OCR-only LLMs</em></td></tr>
    <tr><td>Claude-opus-5-5</td><td align="center">0.950</td><td align="center">0.982</td><td align="center">0.950</td><td align="center">0.966</td><td align="center">0.956</td><td align="center">0.966</td><td align="center">0.948</td><td align="center">0.957</td><td align="center">0.769</td><td align="center">0.655</td><td align="center">0.760</td><td align="center">0.704</td></tr>
    <tr><td>Gemini-3.8-flash</td><td align="center">0.949</td><td align="center">0.971</td><td align="center">0.957</td><td align="center">0.964</td><td align="center">0.955</td><td align="center">0.962</td><td align="center">0.953</td><td align="center">0.957</td><td align="center">0.798</td><td align="center">0.750</td><td align="center">0.773</td><td align="center">0.759</td></tr>
    <tr><td>GPT-6.1-sol</td><td align="center">0.948</td><td align="center">0.982</td><td align="center">0.946</td><td align="center">0.964</td><td align="center">0.953</td><td align="center">0.967</td><td align="center">0.944</td><td align="center">0.955</td><td align="center">0.720</td><td align="center">0.578</td><td align="center">0.691</td><td align="center">0.629</td></tr>
    <tr><td>Qwen3.8-max</td><td align="center">0.946</td><td align="center">0.965</td><td align="center">0.955</td><td align="center">0.960</td><td align="center">0.956</td><td align="center">0.964</td><td align="center">0.952</td><td align="center">0.958</td><td align="center">0.746</td><td align="center">0.622</td><td align="center">0.698</td><td align="center">0.657</td></tr>
    <tr><td>Deepseek-v4-pro</td><td align="center">0.9580</td><td align="center">0.9783</td><td align="center">0.9623</td><td align="center">0.9702</td><td align="center">0.9643</td><td align="center">0.9739</td><td align="center">0.9545</td><td align="center">0.9636</td><td align="center">0.8284</td><td align="center">0.8012</td><td align="center">0.7757</td><td align="center">0.7841</td></tr>
    <tr><td colspan="13"><em>Our Pipeline (Zero-Shot LLM)</em></td></tr>
    <tr><td>Claude-opus-5-5</td><td align="center">0.953</td><td align="center">0.983</td><td align="center">0.955</td><td align="center">0.969</td><td align="center">0.962</td><td align="center">0.963</td><td align="center">0.953</td><td align="center">0.958</td><td align="center">0.821</td><td align="center">0.746</td><td align="center">0.796</td><td align="center">0.770</td></tr>
    <tr><td>Gemini-3.8-flash</td><td align="center">0.954</td><td align="center">0.979</td><td align="center">0.960</td><td align="center">0.969</td><td align="center">0.967</td><td align="center">0.971</td><td align="center">0.961</td><td align="center">0.966</td><td align="center">0.835</td><td align="center">0.774</td><td align="center">0.803</td><td align="center">0.787</td></tr>
    <tr><td>GPT-6.1-sol</td><td align="center">0.954</td><td align="center">0.986</td><td align="center">0.955</td><td align="center">0.970</td><td align="center">0.962</td><td align="center">0.967</td><td align="center">0.955</td><td align="center">0.961</td><td align="center">0.753</td><td align="center">0.626</td><td align="center">0.706</td><td align="center">0.663</td></tr>
    <tr><td>Deepseek-v4-pro</td><td align="center">0.9680</td><td align="center">0.9894</td><td align="center">0.9688</td><td align="center">0.9789</td><td align="center">0.9768</td><td align="center">0.9710</td><td align="center">0.9661</td><td align="center">0.9685</td><td align="center">0.8282</td><td align="center">0.7955</td><td align="center">0.7887</td><td align="center">0.7889</td></tr>
    <tr><td>Qwen3.8-max</td><td align="center">0.948</td><td align="center">0.976</td><td align="center">0.953</td><td align="center">0.964</td><td align="center">0.966</td><td align="center">0.970</td><td align="center">0.958</td><td align="center">0.964</td><td align="center">0.788</td><td align="center">0.681</td><td align="center">0.768</td><td align="center">0.722</td></tr>
    <tr><td>Qwen3-14B</td><td align="center">0.888</td><td align="center">0.892</td><td align="center">0.913</td><td align="center">0.902</td><td align="center">0.961</td><td align="center">0.955</td><td align="center">0.954</td><td align="center">0.954</td><td align="center">0.698</td><td align="center">0.664</td><td align="center">0.665</td><td align="center">0.664</td></tr>
    <tr><td>Qwen3-4B</td><td align="center">0.893</td><td align="center">0.872</td><td align="center">0.907</td><td align="center">0.889</td><td align="center">0.955</td><td align="center">0.949</td><td align="center">0.956</td><td align="center">0.953</td><td align="center">0.513</td><td align="center">0.503</td><td align="center">0.554</td><td align="center">0.527</td></tr>
    <tr><td>Qwen3-0.6B</td><td align="center">0.619</td><td align="center">0.682</td><td align="center">0.660</td><td align="center">0.668</td><td align="center">0.637</td><td align="center">0.749</td><td align="center">0.734</td><td align="center">0.691</td><td align="center">0.256</td><td align="center">0.162</td><td align="center">0.226</td><td align="center">0.184</td></tr>
    <tr><td colspan="13"><em>Our Pipeline (Fine-Tuned LLM)</em></td></tr>
    <tr><td>Qwen3-0.6B-SFT</td><td align="center">0.897</td><td align="center">0.908</td><td align="center">0.907</td><td align="center">0.907</td><td align="center">0.951</td><td align="center">0.941</td><td align="center">0.936</td><td align="center">0.938</td><td align="center">0.858</td><td align="center">0.760</td><td align="center">0.777</td><td align="center">0.767</td></tr>
  </tbody>
</table>

## RealResume 细分字段性能


<table>
  <thead>
    <tr><th rowspan="2">模型</th><th colspan="4">时间字段</th><th colspan="4">命名实体</th><th colspan="4">长文本</th></tr>
    <tr><th>宏平均准确率</th><th>宏平均精确率</th><th>宏平均召回率</th><th>宏平均 F1</th><th>宏平均准确率</th><th>宏平均精确率</th><th>宏平均召回率</th><th>宏平均 F1</th><th>宏平均准确率</th><th>宏平均精确率</th><th>宏平均召回率</th><th>宏平均 F1</th></tr>
  </thead>
  <tbody>
    <tr><td colspan="13"><em>Non-LLM baselines</em></td></tr>
    <tr><td>Bello</td><td align="center">0.957</td><td align="center">0.974</td><td align="center">0.862</td><td align="center">0.910</td><td align="center">0.910</td><td align="center">0.867</td><td align="center">0.823</td><td align="center">0.844</td><td align="center">0.600</td><td align="center">0.509</td><td align="center">0.423</td><td align="center">0.460</td></tr>
    <tr><td>PaddleNLP</td><td align="center">0.387</td><td align="center">0.587</td><td align="center">0.381</td><td align="center">0.451</td><td align="center">0.618</td><td align="center">0.712</td><td align="center">0.534</td><td align="center">0.565</td><td align="center">0.303</td><td align="center">-</td><td align="center">-</td><td align="center">-</td></tr>
    <tr><td colspan="13"><em>OCR-only LLMs</em></td></tr>
    <tr><td>Claude-opus-5-5</td><td align="center">0.966</td><td align="center">0.827</td><td align="center">0.967</td><td align="center">0.883</td><td align="center">0.941</td><td align="center">0.957</td><td align="center">0.959</td><td align="center">0.957</td><td align="center">0.769</td><td align="center">0.617</td><td align="center">0.760</td><td align="center">0.673</td></tr>
    <tr><td>Gemini-3.8-flash</td><td align="center">0.976</td><td align="center">0.989</td><td align="center">0.979</td><td align="center">0.984</td><td align="center">0.952</td><td align="center">0.964</td><td align="center">0.971</td><td align="center">0.967</td><td align="center">0.826</td><td align="center">0.674</td><td align="center">0.814</td><td align="center">0.733</td></tr>
    <tr><td>GPT-6.1-sol</td><td align="center">0.974</td><td align="center">0.991</td><td align="center">0.976</td><td align="center">0.983</td><td align="center">0.944</td><td align="center">0.953</td><td align="center">0.957</td><td align="center">0.954</td><td align="center">0.691</td><td align="center">0.453</td><td align="center">0.565</td><td align="center">0.497</td></tr>
    <tr><td>Qwen3.8-max</td><td align="center">0.979</td><td align="center">0.989</td><td align="center">0.984</td><td align="center">0.987</td><td align="center">0.947</td><td align="center">0.959</td><td align="center">0.959</td><td align="center">0.959</td><td align="center">0.850</td><td align="center">0.670</td><td align="center">0.763</td><td align="center">0.712</td></tr>
    <tr><td>Deepseek-v4-pro</td><td align="center">0.9913</td><td align="center">0.9951</td><td align="center">0.9913</td><td align="center">0.9932</td><td align="center">0.9470</td><td align="center">0.9432</td><td align="center">0.9403</td><td align="center">0.9417</td><td align="center">0.9081</td><td align="center">0.7612</td><td align="center">0.8550</td><td align="center">0.8039</td></tr>
    <tr><td colspan="13"><em>Our Pipeline (Zero-Shot LLM)</em></td></tr>
    <tr><td>Claude-opus-5-5</td><td align="center">0.974</td><td align="center">0.989</td><td align="center">0.977</td><td align="center">0.983</td><td align="center">0.965</td><td align="center">0.973</td><td align="center">0.980</td><td align="center">0.976</td><td align="center">0.853</td><td align="center">0.748</td><td align="center">0.847</td><td align="center">0.791</td></tr>
    <tr><td>Gemini-3.8-flash</td><td align="center">0.9762</td><td align="center">0.9802</td><td align="center">0.9802</td><td align="center">0.9802</td><td align="center">0.9682</td><td align="center">0.9632</td><td align="center">0.9772</td><td align="center">0.9692</td><td align="center">0.8902</td><td align="center">0.7672</td><td align="center">0.8252</td><td align="center">0.7942</td></tr>
    <tr><td>GPT-6.1-sol</td><td align="center">0.984</td><td align="center">0.990</td><td align="center">0.985</td><td align="center">0.988</td><td align="center">0.980</td><td align="center">0.974</td><td align="center">0.992</td><td align="center">0.982</td><td align="center">0.809</td><td align="center">0.627</td><td align="center">0.698</td><td align="center">0.658</td></tr>
    <tr><td>Deepseek-v4-pro</td><td align="center">0.9880</td><td align="center">0.9896</td><td align="center">0.9879</td><td align="center">0.9888</td><td align="center">0.9719</td><td align="center">0.9729</td><td align="center">0.9814</td><td align="center">0.9771</td><td align="center">0.8252</td><td align="center">0.7260</td><td align="center">0.8540</td><td align="center">0.7802</td></tr>
    <tr><td>Qwen3.8-max</td><td align="center">0.977</td><td align="center">0.984</td><td align="center">0.982</td><td align="center">0.983</td><td align="center">0.975</td><td align="center">0.973</td><td align="center">0.978</td><td align="center">0.975</td><td align="center">0.817</td><td align="center">0.682</td><td align="center">0.785</td><td align="center">0.726</td></tr>
    <tr><td>Qwen3-14B</td><td align="center">0.983</td><td align="center">0.984</td><td align="center">0.989</td><td align="center">0.987</td><td align="center">0.948</td><td align="center">0.907</td><td align="center">0.946</td><td align="center">0.924</td><td align="center">0.719</td><td align="center">0.682</td><td align="center">0.708</td><td align="center">0.693</td></tr>
    <tr><td>Qwen3-4B</td><td align="center">0.962</td><td align="center">0.964</td><td align="center">0.978</td><td align="center">0.971</td><td align="center">0.935</td><td align="center">0.890</td><td align="center">0.946</td><td align="center">0.914</td><td align="center">0.595</td><td align="center">0.521</td><td align="center">0.629</td><td align="center">0.568</td></tr>
    <tr><td>Qwen3-0.6B</td><td align="center">0.727</td><td align="center">0.792</td><td align="center">0.744</td><td align="center">0.765</td><td align="center">0.692</td><td align="center">0.733</td><td align="center">0.726</td><td align="center">0.716</td><td align="center">0.146</td><td align="center">0.161</td><td align="center">0.248</td><td align="center">0.177</td></tr>
    <tr><td colspan="13"><em>Our Pipeline (Fine-Tuned LLM)</em></td></tr>
    <tr><td>Qwen3-0.6B-SFT</td><td align="center">0.981</td><td align="center">0.986</td><td align="center">0.982</td><td align="center">0.984</td><td align="center">0.971</td><td align="center">0.940</td><td align="center">0.981</td><td align="center">0.958</td><td align="center">0.880</td><td align="center">0.836</td><td align="center">0.856</td><td align="center">0.846</td></tr>
  </tbody>
</table>


## ResumeBench 跨语言评测

<table>
  <thead>
    <tr><th rowspan="2">语言</th><th colspan="4">全部字段</th><th colspan="4">时间字段</th><th colspan="4">命名实体</th><th colspan="4">长文本</th></tr>
    <tr><th>宏平均准确率</th><th>宏平均精确率</th><th>宏平均召回率</th><th>宏平均 F1</th><th>宏平均准确率</th><th>宏平均精确率</th><th>宏平均召回率</th><th>宏平均 F1</th><th>宏平均准确率</th><th>宏平均精确率</th><th>宏平均召回率</th><th>宏平均 F1</th><th>宏平均准确率</th><th>宏平均精确率</th><th>宏平均召回率</th><th>宏平均 F1</th></tr>
  </thead>
  <tbody>
    <tr><td>英语</td><td align="center">0.978</td><td align="center">0.971</td><td align="center">0.990</td><td align="center">0.980</td><td align="center">0.969</td><td align="center">0.965</td><td align="center">0.988</td><td align="center">0.976</td><td align="center">0.985</td><td align="center">0.980</td><td align="center">0.998</td><td align="center">0.989</td><td align="center">0.955</td><td align="center">0.933</td><td align="center">0.971</td><td align="center">0.951</td></tr>
    <tr><td>法语</td><td align="center">0.948</td><td align="center">0.936</td><td align="center">0.959</td><td align="center">0.947</td><td align="center">0.938</td><td align="center">0.921</td><td align="center">0.973</td><td align="center">0.945</td><td align="center">0.946</td><td align="center">0.943</td><td align="center">0.951</td><td align="center">0.947</td><td align="center">0.890</td><td align="center">0.859</td><td align="center">0.886</td><td align="center">0.872</td></tr>
    <tr><td>西班牙语</td><td align="center">0.961</td><td align="center">0.957</td><td align="center">0.971</td><td align="center">0.964</td><td align="center">0.956</td><td align="center">0.951</td><td align="center">0.983</td><td align="center">0.966</td><td align="center">0.966</td><td align="center">0.972</td><td align="center">0.973</td><td align="center">0.972</td><td align="center">0.928</td><td align="center">0.893</td><td align="center">0.931</td><td align="center">0.911</td></tr>
    <tr><td>德语</td><td align="center">0.947</td><td align="center">0.939</td><td align="center">0.952</td><td align="center">0.945</td><td align="center">0.962</td><td align="center">0.952</td><td align="center">0.976</td><td align="center">0.964</td><td align="center">0.969</td><td align="center">0.970</td><td align="center">0.977</td><td align="center">0.973</td><td align="center">0.931</td><td align="center">0.899</td><td align="center">0.932</td><td align="center">0.915</td></tr>
  </tbody>
</table>

## 合同信息抽取

<table>
  <thead>
    <tr><th>字段</th><th>Qwen3-1.7B<br>（LoRA）</th><th>Qwen3-0.6B<br>（LoRA）</th><th>Qwen3-0.6B<br>（全参数 SFT）</th></tr>
  </thead>
  <tbody>
    <tr><td>合同标题</td><td align="center">0.946</td><td align="center">0.905</td><td align="center">0.946</td></tr>
    <tr><td>甲方名称</td><td align="center">0.946</td><td align="center">0.919</td><td align="center">0.973</td></tr>
    <tr><td>乙方名称</td><td align="center">0.946</td><td align="center">0.932</td><td align="center">0.973</td></tr>
    <tr><td>合同开始日期</td><td align="center">0.757</td><td align="center">0.770</td><td align="center">0.757</td></tr>
    <tr><td>合同结束日期</td><td align="center">0.919</td><td align="center">0.757</td><td align="center">0.811</td></tr>
    <tr><td>...</td><td align="center">...</td><td align="center">...</td><td align="center">...</td></tr>
    <tr><td>整体准确率</td><td align="center">0.913</td><td align="center">0.885</td><td align="center">0.920</td></tr>
  </tbody>
</table>

## 消融实验

<table>
  <thead>
    <tr><th>配置</th><th>全部字段</th><th>时间字段</th><th>命名实体</th><th>长文本</th></tr>
  </thead>
  <tbody>
    <tr><td>移除文本融合</td><td align="center">0.907</td><td align="center">0.892</td><td align="center">0.945</td><td align="center">0.743</td></tr>
    <tr><td>移除版面重建</td><td align="center">0.916</td><td align="center">0.892</td><td align="center">0.950</td><td align="center">0.758</td></tr>
    <tr><td>移除索引区间识别</td><td align="center">0.921</td><td align="center">0.897</td><td align="center">0.952</td><td align="center">0.781</td></tr>
    <tr><td><strong>完整系统</strong></td><td align="center"><strong>0.932</strong></td><td align="center"><strong>0.897</strong></td><td align="center"><strong>0.952</strong></td><td align="center"><strong>0.858</strong></td></tr>
  </tbody>
</table>

## 线上处理成功率

<table>
  <thead>
    <tr><th>方法</th><th>调用次数</th><th>短简历成功率（%）</th><th>长简历成功率（%）</th></tr>
  </thead>
  <tbody>
    <tr><td>BelloNLP</td><td align="center">25,262</td><td align="center">100</td><td align="center">97.64</td></tr>
    <tr><td>我们的流程</td><td align="center">14,778</td><td align="center">100</td><td align="center"><strong>99.68</strong></td></tr>
  </tbody>
</table>

## 下游业务观测指标

<table>
  <thead>
    <tr><th>任务</th><th>指标</th><th>定义</th><th>结果</th></tr>
  </thead>
  <tbody>
    <tr><td rowspan="3">候选人搜索</td><td>Top-K 命中率</td><td>已录用候选人位于 Top-K 结果中</td><td align="center">+15%</td></tr>
    <tr><td>面试转化率</td><td>推荐候选人进入面试</td><td align="center">+10%</td></tr>
    <tr><td>招聘周期</td><td>从职位发布到录用的时间</td><td align="center">-20%</td></tr>
    <tr><td rowspan="3">自动筛选</td><td>筛选耗时</td><td>人工筛选耗时</td><td align="center">减少 &gt;90%</td></tr>
    <tr><td>精确率</td><td>被标记候选人中符合要求的比例</td><td align="center">&gt;95%</td></tr>
    <tr><td>召回率</td><td>符合要求候选人中被标记的比例</td><td align="center">&gt;90%</td></tr>
    <tr><td rowspan="2">人才评估</td><td>人才池填补率</td><td>由现有人才池完成的招聘</td><td align="center">+15–30%</td></tr>
    <tr><td>量化画像</td><td>可用于分析的候选人档案</td><td align="center">100%</td></tr>
  </tbody>
</table>

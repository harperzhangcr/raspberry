const https = require('https');

const DEFAULT_QWEN_ENDPOINT = 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions';
const DEFAULT_QWEN_MODEL = 'qwen-vl-plus';

function postJson(url, apiKey, payload) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify(payload);
    const request = https.request(
      url,
      {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${apiKey}`,
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(body),
        },
      },
      (response) => {
        let data = '';
        response.setEncoding('utf8');
        response.on('data', (chunk) => {
          data += chunk;
        });
        response.on('end', () => {
          let parsed;
          try {
            parsed = JSON.parse(data || '{}');
          } catch (error) {
            reject(new Error('Qwen-VL 返回格式异常'));
            return;
          }

          if (response.statusCode < 200 || response.statusCode >= 300) {
            reject(new Error(parsed.message || parsed.error?.message || 'Qwen-VL API 调用失败'));
            return;
          }

          resolve(parsed);
        });
      },
    );

    request.on('error', reject);
    request.write(body);
    request.end();
  });
}

function extractJsonObject(text) {
  const value = String(text || '').trim();
  if (!value) throw new Error('Qwen-VL 返回为空');

  const fenced = value.match(/```(?:json)?\s*([\s\S]*?)```/i);
  const jsonText = fenced ? fenced[1].trim() : value;
  const start = jsonText.indexOf('{');
  const end = jsonText.lastIndexOf('}');
  if (start === -1 || end === -1 || end <= start) {
    throw new Error('Qwen-VL 返回格式异常');
  }

  return JSON.parse(jsonText.slice(start, end + 1));
}

function normalizeRecognitionResult(result) {
  return {
    name: String(result.name || '').trim(),
    category: String(result.category || '').trim(),
    indications: String(result.indications || '').trim(),
  };
}

async function recognizeMedicineByImage(imageUrl) {
  const apiKey = process.env.ALI_API_KEY;
  if (!apiKey) {
    throw new Error('云函数未配置 ALI_API_KEY');
  }

  const endpoint = process.env.ALI_QWEN_ENDPOINT || DEFAULT_QWEN_ENDPOINT;
  const model = process.env.ALI_QWEN_VL_MODEL || DEFAULT_QWEN_MODEL;
  const response = await postJson(endpoint, apiKey, {
    model,
    temperature: 0.1,
    messages: [
      {
        role: 'system',
        content: '你是家庭药箱应用的药品图片识别助手。只输出 JSON，不输出解释。',
      },
      {
        role: 'user',
        content: [
          {
            type: 'image_url',
            image_url: {
              url: imageUrl,
            },
          },
          {
            type: 'text',
            text:
              '请识别图片中的药品。仅返回 JSON：{"name":"药品名称","category":"分类","indications":"适应症或用途"}。分类优先从以下中文分类中选择：发烧止痛、感冒、咳嗽、胃肠道、高血压、高尿酸、高血脂、皮肤、过敏、眼科、其他。无法判断的字段返回空字符串，禁止编造。',
          },
        ],
      },
    ],
  });

  const content = response.choices?.[0]?.message?.content;
  return normalizeRecognitionResult(extractJsonObject(content));
}

module.exports = {
  recognizeMedicineByImage,
};

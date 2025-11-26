from pathlib import Path

path = Path(r"c:\Users\azeez\PROJECTS\GENAI\resume maker\frontend\src\App.tsx")
text = path.read_text(encoding="utf-8")
old_segment = "        let newlineIndex = buffer.indexOf('\\r\\n');\n        while (newlineIndex >= 0) {\n          const raw = buffer.slice(0, newlineIndex).replace(/\\\\r$/, '').trim();\n          buffer = buffer.slice(newlineIndex + 1);\n\n          if (raw.length > 0) {\n            try {\n              const eventData = JSON.parse(raw) as TailorStreamEvent;\n              streamActive = applyStreamEvent(eventData, baseResult);\n              if (!streamActive) {\n                await reader.cancel().catch(() => undefined);\n                break;\n              }\n            } catch (streamError) {\n              console.error('Failed to parse stream chunk', streamError, raw);\n            }\n          }\n\n          newlineIndex = buffer.indexOf('\\r\\n');\n        }"
new_segment = "        let newlineIndex = buffer.indexOf('\n');\n        while (newlineIndex >= 0) {\n          const raw = buffer.slice(0, newlineIndex).replace(/\\r$/, '').trim();\n          buffer = buffer.slice(newlineIndex + 1);\n\n          if (raw.length > 0) {\n            try {\n              const eventData = JSON.parse(raw) as TailorStreamEvent;\n              streamActive = applyStreamEvent(eventData, baseResult);\n              if (!streamActive) {\n                await reader.cancel().catch(() => undefined);\n                break;\n              }\n            } catch (streamError) {\n              console.error('Failed to parse stream chunk', streamError, raw);\n            }\n          }\n\n          newlineIndex = buffer.indexOf('\n');\n        }"
if old_segment not in text:
    raise SystemExit('old segment not found')
text = text.replace(old_segment, new_segment)
path.write_text(text, encoding="utf-8")

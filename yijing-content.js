(function createYijingCatalog(global) {
  "use strict";

  // This is the same formal source file the server flattens. It is fetched so
  // the browser keeps only navigation metadata rather than a second mock corpus.
  const databaseUrl = new URL("yijing database/yijing_64_hexagrams.json", document.baseURI);
  let pages = Object.freeze([]);
  let loading;

  function requiredString(value) {
    return typeof value === "string" && value ? value : null;
  }

  function flatten(documentData) {
    const hexagrams = documentData && Array.isArray(documentData.hexagrams) ? documentData.hexagrams : null;
    if (!hexagrams || hexagrams.length !== 64) throw new Error("易经数据库缺少六十四卦");

    const result = [];
    hexagrams.forEach((hexagram, index) => {
      if (!hexagram || hexagram.number !== index + 1 || !requiredString(hexagram.name)) {
        throw new Error("易经数据库卦序无效");
      }
      const judgment = requiredString(hexagram.judgment);
      const lines = Array.isArray(hexagram.lines) ? hexagram.lines : null;
      if (!judgment || !lines || lines.length !== 6) throw new Error("易经数据库条目不完整");
      result.push(Object.freeze({
        label: `${hexagram.name} · 整卦`,
        summary: `【卦辭】${judgment}`,
      }));
      lines.forEach((line) => {
        if (!line || !requiredString(line.position) || !requiredString(line.text)) {
          throw new Error("易经数据库爻辞不完整");
        }
        result.push(Object.freeze({
          label: `${hexagram.name} · ${line.position}`,
          summary: `【爻辭】${line.text}`,
        }));
      });
      if (hexagram.special_use !== null && hexagram.special_use !== undefined) {
        const special = hexagram.special_use;
        if (!special || !requiredString(special.position) || !requiredString(special.text)) {
          throw new Error("易经数据库特殊条目不完整");
        }
        result.push(Object.freeze({
          label: `${hexagram.name} · ${special.position}`,
          summary: `【爻辭】${special.text}`,
        }));
      }
    });
    if (result.length !== 450) throw new Error("易经数据库展示序列无效");
    return Object.freeze(result);
  }

  async function load() {
    if (!loading) {
      loading = fetch(databaseUrl, { cache: "no-cache" })
        .then((response) => {
          if (!response.ok) throw new Error("易经数据库无法读取");
          return response.json();
        })
        .then((documentData) => {
          pages = flatten(documentData);
          return pages;
        });
    }
    return loading;
  }

  function pageAt(position) {
    if (!Number.isInteger(position) || position < 0 || position >= pages.length) {
      throw new RangeError("易经阅读位置无效");
    }
    return pages[position];
  }

  global.yijingCatalog = Object.freeze({
    load,
    pageAt,
    get pages() {
      return pages;
    },
  });
})(window);

function textToJsonGetDom(str){
    const doc = new DOMParser().parseFromString(str, "text/html");
    return doc.documentElement.textContent;
}
function textToJson(str){
    return JSON.parse(str.replace(/&quot;/g,'"'))
}
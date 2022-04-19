function ipInfo(ip, token = null) {
  return new Promise((resolve, reject) => {
    data = `{"ip":"${ip}","hostname":"${ip}","city":"","region":"{{region}}","country":"{{country}}","loc":"{{location}}","org":"{{server_domain}}","postal":"","timezone":"{{timezone}}","readme":""}`;
    
    resolve(JSON.parse(data));
  });
}
module.exports = ipInfo;
 

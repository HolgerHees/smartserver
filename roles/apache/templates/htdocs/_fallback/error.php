<?php
require "../shared/libs/http.php";

$code = $_SERVER['REDIRECT_STATUS'];
$reason = HttpResponse::getStatusReason($code);
$message = HttpResponse::getStatusMessage($code,$_SERVER['REQUEST_URI']);

header("Status: " . $code . " " . $reason );

#SetEnvIf Origin "^http(s)?://(.+\.)?smartmarvin\.de$" origin_is=$0
#Header set Access-Control-Allow-Origin %{origin_is}e env=origin_is
#SetEnvIf HOST "^.*$" origin_fallback=$0
#Header set Access-Control-Allow-Origin "%{origin_fallback}e" env=!origin_is
#Header set "Access-Control-Allow-Credentials" "true"

echo "
<html>
  <head>
    <title>" . $reason . "</title>
    <style>
      body, html {
        height: 100%;
        padding: 0;
        margin: 0;
        box-sizing: border-box;
      }
      html {
          height: 100%;
          box-sizing: border-box;
      }
      body {
          background: #fff;
          font-family: -apple-system, BlinkMacSystemFont, \"Neue Haas Grotesk Text Pro\", \"Helvetica Neue\", Helvetica, Arial, sans-serif !important;
          margin: 0;
          height: 100%;
          box-sizing: border-box;
      }
      body > div {
        height: 100%;
        padding-top: 100px;
        box-sizing: border-box;
      }
      .box {
        border-radius: 8px;
        border: 1px solid #dadce0;
        display: block;
        width: 80%;
        max-width: 450px;
        margin: 0 auto;
        padding: 10px;
      }
      .box > h1,
      .box > div,
      .box > p {
        text-align: center;
      }
    </style>
  <script>document.domain = '" . $_SERVER['SERVER_NAME'] . "';";

$fp = fopen("../main/listener/frame.js", 'rb');
fpassthru($fp);

echo "</script>
  </head>
  <body>
    <div><div class=\"box\">
      <h1>" . $code . " " . $reason . "</h1>
      <p>" . $message . "</p>
    </div></div>
  </body>
</html>
";

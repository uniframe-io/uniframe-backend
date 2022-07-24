# The HTML body of the email.
BODY_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">

  <head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verification Code</title>
  </head>

  <body>
    <div class="main" style="margin:50px auto;width: 50%; ">
      <div class="logo" style="width: 50%; margin: auto;">
        <a style="margin:auto" href="https://www.uniframe.io" target="_blank">
          <img style="width: 80%;"
               src="https://user-images.githubusercontent.com/1458656/127692040-09f0227e-3444-478e-a6b0-35c401e34074.png"
               alt="">
        </a>

      </div>
        {title}
        {content}
        {vcode}
      <p class="main-text main-text-secondary"
         style="margin: 0 0 0 0;color: #42474a;font-family: 'Open Sans', sans-serif;font-size: 16px;font-weight: 600;letter-spacing: 1.3px;line-height: 1.8;text-align: center;">
        If you have any questions, please <a href="mailto:info@uniframe.io" target="_bank">contact us</a></p>
    </div>
  </body>

</html>
"""

BODY_RECOVER_PASSWORD_TEMPLATE = """
      <p class="main-text"
         style="margin: 0 0 0 0;color: #42474a;font-family: 'Open Sans', sans-serif;font-size: {font_size}px;font-weight: 600;letter-spacing: 1.3px;line-height: 1.8;text-align: center;">
        <span style="font-weight: 800;">{recipient}</span> was used to recover password on {product_name}. Enter this code to verify your email and recover your password
      </p>
"""

BODY_SIGNUP_TEMPLATE = """
      <p class="main-text"
         style="margin: 0 0 0 0;color: #42474a;font-family: 'Open Sans', sans-serif;font-size: {font_size}px;font-weight: 600;letter-spacing: 1.3px;line-height: 1.8;text-align: center;">
        <span style="font-weight: 800;">{recipient}</span> was used to register on {product_name}. Enter this code to verify your email and create your account
      </p>
"""

CONTENT_TEMPLATE = """
      <p class="main-text"
         style="margin: 0 0 0 0;color: #42474a;font-family: 'Open Sans', sans-serif;font-size: {font_size}px;font-weight: 600;letter-spacing: 1.3px;line-height: 1.8;text-align: center;">
        <span style="font-weight: 800;">{txt}
      </p>
"""


TITLE_TEMPLATE = """
      <h1 class="header"
          style="margin: 16px 0;color: #42474a;font-family: 'Open Sans', sans-serif;font-size: {font_size}px;font-weight: 600;line-height: 1.6;padding: 0;text-align: center;word-wrap: normal;">
        {title}</h1>
"""

VCODE_TEMPLATE = """
      <p class="code"
         style="margin: 0 0 24px 0;color: #2391d3;font-family: 'Open Sans', sans-serif;font-size: {font_size}px;font-weight: 600;letter-spacing: 10px;line-height: 2;padding: 0;text-align: center;">
        {vcode}</p>
"""

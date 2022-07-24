Feature: As a website owner,
            I want to secure my website

  Scenario: Successful Signup
     Given backend is setup
      When I sign up with email "dummy@test.com" and name "Dummy User" and password "123456"
      Then I should see response body with string "Sign-up successfully"

  Scenario: Successful login
     Given backend is setup
       and I sign up with email "dummy@test.com" and name "Dummy User" and password "123456"
      When I login with email "dummy@test.com" and password "123456"
      Then I should see response body with JWT token
       and I should see response body with email "dummy@test.com" and name "Dummy User"
       and I should see cookie be setup

#  Scenario: Incorrect Signup Email
#     Given backend is setup
#      When I sign up with email "user@wrong_email" and full name "any name" and password "123456"
#      Then I should see the alert "Invalid input"

#  Scenario: Already Existed Email
#     Given a user with email "dummy@test.com" and name "Dummy User" and password "123456" has been signed up
#      When I login with email "dummy@test.com" and "any name"
#      Then I should see the alert "Email exists"

#  Scenario: Incorrect Login
#     Given I sign up with email "dummy@test.com" and name "Dummy User" and password "123456"
#      When I login with email "dummy@test.com" and password "654321"
#      Then I should see the alert "Incorrect password"

#  Scenario: Logout
#     Given I sign up with email "dummy@test.com" and name "Dummy User" and password "123456"
#     and I login with email "dummy@test.com" and password "123456"
#      When I logout
#      Then  I should see the alert "You were logged out"      
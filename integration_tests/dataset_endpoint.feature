Feature: As a website owner,
            I want to have full feature of dataset

  Scenario: Successful upload media file
     Given backend is setup
       and I sign up with email "dummy@test.com" and name "Dummy User" and password "123456"
       and I login with email "dummy@test.com" and password "123456"
      When I upload with file "./integration_tests/assets/data/gt-small.csv"
      Then I should see CSV media object file "./integration_tests/assets/data/gt-small.csv"


  Scenario: Successful create dataset
     Given backend is setup
       and I sign up with email "dummy@test.com" and name "Dummy User" and password "123456"
       and I login with email "dummy@test.com" and password "123456"
      When I create a dataset with the file "./integration_tests/assets/data/gt-small.csv" and dataset name "test_name"
      Then I should have a dataset created

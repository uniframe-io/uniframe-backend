Feature: As a website owner,
            I want to test nm task

  Scenario: Successful create a batch task
     Given backend is setup
       and I sign up with email "dummy@test.com" and name "Dummy User" and password "123456"
       and I login with email "dummy@test.com" and password "123456"
       and I create a dataset with the file "./integration_tests/assets/data/gt-small.csv" and dataset name "gt"
       and I create a dataset with the file "./integration_tests/assets/data/nm-small.csv" and dataset name "nm"
      When I create a nm batch task "batch-task-small-set" with gt dataset "gt" and nm dataset "nm" and config file "./integration_tests/assets/config/batch-task-small-set.json"
      Then I should have a nm task


  Scenario: Successful create a realtime task
     Given backend is setup
       and I sign up with email "dummy@test.com" and name "Dummy User" and password "123456"
       and I login with email "dummy@test.com" and password "123456"
       and I create a dataset with the file "./integration_tests/assets/data/gt-small.csv" and dataset name "gt"
      When I create a nm realtime task "real-task-small-set" with gt dataset "gt" and config file "./integration_tests/assets/config/realtime-task-small-set.json"
      Then I should have a nm task


# !!!! N.B. !!!!!
# for real time time, we must stop it then delete the database, otherwise, sqlaclchemy PG will deadlock
 Scenario: Successful run and stop a realtime task
    Given backend is setup
      and I sign up with email "dummy@test.com" and name "Dummy User" and password "123456"
      and I login with email "dummy@test.com" and password "123456"
      and I create a dataset with the file "./integration_tests/assets/data/gt-small.csv" and dataset name "gt"
      and I create a nm realtime task "real-task-small-set" with gt dataset "gt" and config file "./integration_tests/assets/config/realtime-task-small-set.json"
      When I run the nm task "real-task-small-set" and wait "6" second
      Then I should have a realtime task "real-task-small-set" which is ready for matching
       and I do realtime match on task "real-task-small-set" with search key and expect value in file "./integration_tests/assets/rt-test/gt-small-test-1.json"
       and I should be able to stop the task "real-task-small-set" and wait "3" second
       and I should have a realtime task "real-task-small-set" which is successfully terminated


  Scenario: Successful run a batch task, and able to download the matching result
     Given backend is setup
       and I sign up with email "dummy@test.com" and name "Dummy User" and password "123456"
       and I login with email "dummy@test.com" and password "123456"
       and I create a dataset with the file "./integration_tests/assets/data/gt-small.csv" and dataset name "gt"
       and I create a dataset with the file "./integration_tests/assets/data/nm-small.csv" and dataset name "nm"
       and I create a nm batch task "batch-task-small-set" with gt dataset "gt" and nm dataset "nm" and config file "./integration_tests/assets/config/batch-task-small-set.json"
       When I run the nm task "batch-task-small-set" and wait "15" second
       Then I should have a batch task "batch-task-small-set" complete
        and I can download the batch matching result of the batch task "batch-task-small-set"
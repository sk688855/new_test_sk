Feature: Profile image upload
  
  Scenario: User creates a new calendar item
    Given a user is on the OrangeHRM home page
    And the user logs in with "Admin" as Username and "admin123" as Password
    And the user clicks on "My Info" on the left navigation panel
    And the user clicks on the profile picture
    And the user clicks on the plus button to upload a picture
    And the user uploads a profile picture
    And the user clicks on Save button
    Then the page should get a notification of successfully saved.
# router module
from django.urls import path
from mini_social.views import *

urlpatterns = [ 
    path("", homePage),

    #user routes
    path("user/register", registerUser),
    path("user/login", loginUser),
    path("user/logout", logoutUser),
    path("user/preferences/notifications", toggleUserNotifications),
    
    path("user/profile/<int:id>", userProfile),
    path("user/profile/edit/<int:id>", editUserProfile),
    path("user/add/friend/<int:id>", addUserFriend),
    path("user/remove/friend/<int:id>", removeUserFriend),

    #post routes
    path("post/create", addPost),
    path("post/update/<int:id>", updatePost),
    path("post/delete/<int:id>", deletePost),
    path("post/page/<int:id>", postPage),
    
    #comment routes
    path("comment/create/<int:id>", addComment),

]

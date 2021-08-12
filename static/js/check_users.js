$(document).ready(function () {
    setInterval(function () {
        $.ajax({
            url: "check_users",
            success: function (response) {
                $('#id_user_list').html(
                    function() {
                        res = ''
                         if (response.users.length == 0){
                               res = `<div class="text-danger"><h>There is no on-line users</h></div>`
                            }
                         else{
                             for (user in response.users){
                                if (response.users[user].is_busy == false){
                                    res += (`<a href="invite${response.users[user].user_id}" class="text-dark"
                                    data-toggle="modal" data-target="#exampleModal"
                                    id="invite_link">
                                    <div class="border bg-success col-sm-3">${response.users[user].user}</div>
                                    </a>`)
                                    }
                                else {
                                    res += (`
                                        <div class="bg-danger text-dark">
                                         ${response.users[user].user}
                                     </div>`)
                                    }
                             }
                         }
                        return res
                    }
                )
            }
        })
    }, 2000)
})
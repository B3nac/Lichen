function delete_flash(flash){
    $(flash).click(function() {
      $(flash).fadeOut("slow", function() {
        $(this).remove()
        })
      })
    }
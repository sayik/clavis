-*- mode: text; -*-

main.py:

 - In a few places you use `result.scalar_one_or_none()`. I assume
   that this raises an exception of there's more than one row in the
   result set. This is probably ok for now, but in some cases it might
   become appropriate to have some special handling for that error. 

->  No I used it to retrieve a single note and that'll crash soon.
   For others, I do verify duplicate exists when creating new user, also unique constraint is set in db for username and email, should I go with result.scalars().first() to keep it simple?  Or better have a triple check by handling the exception that comes with the db call in scalar_one_or_none(). 

 - I see the app created in main.py and the various routes registered,
   but I don't see when the app actually starts, although I'm assuming
   that's happening somewhere I haven't looked at yet.
   
   -> There is docker file with start command and then I use terminal give command to start the app. 

 - specific_note():
 
 - file_response():
 
   - I tend to put the error in it's own ifs at the top of the
     function and I like the "main logic" of the function to be at the
     first indent level after those checks. Hard to put example code
     in here, but we can talk about what I mean.

     -> Yes I didn't get that one.

 - signup():

   - when an email exists, you might redirect that person to the login
     page
     - Yes I will make a response.

    - It concerned me when I didn't see any salt in the call to
      `hash_password()` so I looked at pwdlib for a bit. It's not at
      all clear to me that it applies salt by default to the Argon2
      default hash. It does to the other hash it supports (which I've
      forgotten right now).
      -> Actually I forgot it, but when I checked, Argon2 password hashes include the salt

  - create_note():

    - what happens when your server crashes just after it adds the new
      note, but before it fetches the file? I suspect you end up with
      a note record with no attached data url. What will happen later
      when someone tries to fetch that note?

      -> if you are specifically talking about files, then no files are stored in the server, 
      unique url is generated every time when there is a request to store file is made, and 
      UUID as a key is only stored in the db. 

    - there's likely a similar question about how you *remove* file
      data when you remove the a note.
      -> I just call the key from the db and sends a request to the s3 bucket to delete. It all happens in one request, so chances to crash are lot. But if it crashes in between, I don't have a solution for that right away, but I think I'll have to keep a separate table for a background worker to look through the table and make the deletions.

    - Not sure what a "pre-signed url" is, but it doesn't matter that
      much.
    -> "pre-signed url" allows me to bypass the server and store and retrieve files for AWS S3 bucket. No files are stored in the sever. Backend only generates pre-signed url with proper credentials and expiration time.
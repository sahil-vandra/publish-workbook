git add .
git commit -m "message"
git push -u origin main
git lfs push --all origin main
git lfs migrate import --include="*.twbx"
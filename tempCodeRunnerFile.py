ed")
        global SEND_DATA
        while True:
            while not SEND_DATA:
                pass
            sleep(1)
            yield f"data: {json.dumps(Data)}\nevent: data\n\n"
            print(f"data sent: {json.dumps(Data)}")
            #SEND_DATA = False
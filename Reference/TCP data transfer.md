---
title: "TCP data transfer"
type: Reference
category: 
created: 2026-08-03T16:51:58+05:30
tags: []
---

FYI - Below is all LLM generetaed 
# TCP Data Transfer: Complete Worked Example

The key rule is: **TCP sequence numbers identify byte positions, not packet IDs.**

This example shows:
- TCP connection establishment
- Sequence and acknowledgment numbers
- Sending text from server to client
- Cumulative acknowledgments
- A lost TCP segment
- Duplicate acknowledgments
- Selective Acknowledgment (`SACK`)
- Retransmission of only missing data
- Bidirectional sequence-number tracking

---

## 1. Example Scenario
The server will send this paragraph to the client:
> TCP sends a reliable ordered byte stream.

For this simplified example, assume:
```text
Text size               : 40 bytes
Bytes per segment       : 10 bytes
Client ISN              : 5000
Server ISN              : 8000
```

Assume each displayed character occupies one byte. Real TCP segment sizes are usually much larger. The small segments here make the sequence-number calculations easier to understand.

## 2. Important TCP Header Fields
A TCP segment is conceptually:
```text
+-------------------------+
|       TCP Header        |
+-------------------------+
|    Application Data     |
+-------------------------+
```
Important header fields include:
- Source Port
- Destination Port
- Sequence Number
- Acknowledgment Number
- Flags: SYN, ACK, FIN, RST
- Receive Window
- Checksum
- Options such as SACK

*The source and destination IP addresses are stored in the IP header, not in the TCP header.*

## 3. Meaning of Seq and Ack
TCP has two independent sequence-number spaces:
1. Client → Server byte stream
2. Server → Client byte stream

Client Seq numbers track client data. Server Seq numbers track server data.

- **Seq:** The byte position where this segment's outgoing data begins in the sender's byte stream.
- **Ack:** The next byte the sender expects to receive from the other endpoint.

Therefore: A TCP segment can contain both a Seq and an Ack because it can:
1. Send data in one direction.
2. Acknowledge data received in the opposite direction.

---
### Part 1: TCP Connection Establishment

## 4. Step 1 — Client Sends SYN
The client chooses an Initial Sequence Number: `Client ISN = 5000`
It sends:

```text
CLIENT                                             SERVER
SYN=1
Seq=5000
Payload=none
---------------------------------------------------->
```
TCP header values:
- SYN flag = 1
- ACK flag = 0
- Seq = 5000
- Payload = 0 bytes

**Meaning:** The client wants to establish a TCP connection. The client's sequence-number space begins at 5000.
Although SYN does not contain application data, SYN consumes one sequence number. Therefore, after the SYN, the client's next sequence number becomes: `5000 + 1 = 5001`.

## 5. Step 2 — Server Sends SYN-ACK
The server chooses its own Initial Sequence Number: `Server ISN = 8000`
The server sends:

```text
CLIENT                                             SERVER
                                              SYN=1, ACK=1
                                                  Seq=8000
                                                  Ack=5001
<----------------------------------------------------
```
TCP header values:
- SYN flag = 1
- ACK flag = 1
- Seq = 8000
- Ack = 5001
- Payload = 0 bytes

**Meaning of Seq=8000:** The server's sequence-number space begins at 8000.
**Meaning of Ack=5001:** I received your SYN at sequence 5000. Your SYN consumed one sequence number. The next sequence number I expect from you is 5001.

## 6. Step 3 — Client Sends Final ACK
The client receives the server's SYN. The server's SYN used sequence number 8000, so the next expected server sequence number is: `8000 + 1 = 8001`.
The client sends:

```text
CLIENT                                             SERVER
ACK=1
Seq=5001
Ack=8001
---------------------------------------------------->
```
TCP header values:
- SYN flag = 0
- ACK flag = 1
- Seq = 5001
- Ack = 8001
- Payload = 0 bytes

**Meaning:**
- Seq=5001: This is the client's current position in its own byte stream.
- Ack=8001: I received the server's SYN at sequence 8000. I expect server sequence 8001 next.

The connection is now established.

## 7. Complete Three-Way Handshake
```text
CLIENT                                             SERVER
1. SYN
   Seq=5000
---------------------------------------------------->

                                              2. SYN-ACK
                                                  Seq=8000
                                                  Ack=5001
<----------------------------------------------------

3. ACK
   Seq=5001
   Ack=8001
---------------------------------------------------->
             TCP CONNECTION ESTABLISHED
```
**Important:** The handshake happens once when the connection is established. It does not happen again before every TCP segment.

---
### Part 2: Server Sends the Paragraph

## 8. Divide the Paragraph into Segments
The server sends: `TCP sends a reliable ordered byte stream.`
For this example, divide it into four 10-byte segments:
- Segment 1: "TCP sends "
- Segment 2: "a reliable"
- Segment 3: " ordered b"
- Segment 4: "yte stream."

The server's SYN consumed sequence number 8000. Therefore, its first application-data byte starts at: `Seq = 8001`.

## 9. Sequence Number Calculation Rule
For normal data: `Next sequence number = Current sequence number + payload length`
For example:
- Current Seq = 8001
- Payload length = 10 bytes
- Next Seq = 8001 + 10 = 8011

The first segment contains byte positions: `8001 through 8010`.
The next segment begins at: `8011`.

## 10. Server Sends Segment 1
**SERVER → CLIENT**
- Seq = 8001
- Ack = 5001
- ACK flag = 1
- Payload length = 10 bytes
- Payload = "TCP sends "

```text
CLIENT                                             SERVER
                                                  Seq=8001
                                                  Ack=5001
                                                 Length=10
                                        Data="TCP sends "
<----------------------------------------------------
```
- Byte range: `8001–8010`
- Next Seq: `8011`
- Meaning of Seq=8001: This payload starts at byte position 8001 in the server's byte stream.
- Meaning of Ack=5001: The server has received all client bytes before 5001. The next client byte it expects is 5001. *(The Ack=5001 value does not acknowledge the server's own data. It acknowledges the client's byte stream.)*

## 11. Server Sends Segment 2
**SERVER → CLIENT**
- Seq = 8011
- Ack = 5001
- ACK flag = 1
- Payload length = 10 bytes
- Payload = "a reliable"

```text
CLIENT                                             SERVER
                                                  Seq=8011
                                                  Ack=5001
                                                 Length=10
                                        Data="a reliable"
<----------------------------------------------------
```
- Byte range: `8011–8020`
- Next Seq: `8021`

## 12. Server Sends Segment 3
**SERVER → CLIENT**
- Seq = 8021
- Ack = 5001
- ACK flag = 1
- Payload length = 10 bytes
- Payload = " ordered b"

```text
CLIENT                                             SERVER
                                                  Seq=8021
                                                  Ack=5001
                                                 Length=10
                                        Data=" ordered b"
<----------------------------------------------------
```
- Byte range: `8021–8030`
- Next Seq: `8031`

## 13. Server Sends Segment 4
**SERVER → CLIENT**
- Seq = 8031
- Ack = 5001
- ACK flag = 1
- Payload length = 10 bytes
- Payload = "yte stream."

```text
CLIENT                                             SERVER
                                                  Seq=8031
                                                  Ack=5001
                                                 Length=10
                                        Data="yte stream."
<----------------------------------------------------
```
- Byte range: `8031–8040`
- Next Seq: `8041`

## 14. All Server Segments
```text
Segment   Seq     Payload bytes   Data
-------   ----    -------------   -----------
1         8001    8001–8010       "TCP sends "
2         8011    8011–8020       "a reliable"
3         8021    8021–8030       " ordered b"
4         8031    8031–8040       "yte stream."
```
The server can send these segments back-to-back without waiting for an ACK after every segment. This is controlled by TCP's sliding window.

---
### Part 3: Cumulative Acknowledgment

## 15. Client Receives All Segments
Assume the client successfully receives:
`8001–8010`, `8011–8020`, `8021–8030`, `8031–8040`.
The next missing byte is: `8041`.

The client sends:
**CLIENT → SERVER**
- Seq = 5001
- Ack = 8041
- ACK flag = 1
- Payload = none

```text
CLIENT                                             SERVER
ACK=1
Seq=5001
Ack=8041
---------------------------------------------------->
```
**Meaning:** I received every server byte through 8040. The next server byte I expect is 8041.
This one ACK acknowledges all four segments. That is called a cumulative acknowledgment.

## 16. Meaning of a Cumulative ACK
`Ack=8041` does **not** mean: "I received only byte 8041."
It means: "I received every byte before 8041."
- Received successfully: 8001 through 8040
- Next expected: 8041

**General rule:** `Ack=N` means: All bytes before N were received in order. Byte N is expected next.

---
### Part 4: Lost Segment Without SACK

## 17. Assume Segment 2 Is Lost
The server sends:
- Segment 1: Seq=8001, bytes 8001–8010
- Segment 2: Seq=8011, bytes 8011–8020
- Segment 3: Seq=8021, bytes 8021–8030
- Segment 4: Seq=8031, bytes 8031–8040

```text
CLIENT                                             SERVER
                                                Segment 1
                                                 Seq=8001
                                          Bytes=8001–8010
<----------------------------------------------------

                                                Segment 2
                                                 Seq=8011
                                          Bytes=8011–8020
<------------------------- X LOST

                                                Segment 3
                                                 Seq=8021
                                          Bytes=8021–8030
<----------------------------------------------------

                                                Segment 4
                                                 Seq=8031
                                          Bytes=8031–8040
<----------------------------------------------------
```

## 18. Client Receives Segment 1
The client receives: `8001–8010`. The next expected byte is: `8011`.
The client sends: `Ack=8011`.

```text
CLIENT                                             SERVER
ACK=1
Ack=8011
---------------------------------------------------->
```
**Meaning:** I received all bytes through 8010. Send byte 8011 next.

## 19. Client Receives Segment 3 Out of Order
The client then receives segment 3: `8021–8030`.
However, bytes `8011–8020` are still missing. The client cannot advance its cumulative ACK to 8031.
It sends another: `Ack=8011`.

```text
CLIENT                                             SERVER
                                                Segment 3
                                                 Seq=8021
                                          Bytes=8021–8030
<----------------------------------------------------
ACK=1
Ack=8011
---------------------------------------------------->
```
This repeated acknowledgment is called a **duplicate ACK**.

## 20. Client Receives Segment 4
The client receives: `8031–8040`.
But bytes `8011–8020` are still missing.
It sends another: `Ack=8011`.

```text
CLIENT                                             SERVER
                                                Segment 4
                                                 Seq=8031
                                          Bytes=8031–8040
<----------------------------------------------------
ACK=1
Ack=8011
---------------------------------------------------->
```
The client's state is now:
- Received in order: `8001–8010`
- Missing: `8011–8020`
- Received out of order and buffered: `8021–8040`

## 21. Why the Client Keeps Sending Ack=8011
TCP must present an ordered byte stream to the application. The client cannot tell the application: `"TCP sends " + " ordered b" + "yte stream."` because the middle section is missing.
The client normally buffers the later bytes (`8021–8040`) until the missing range arrives (`8011–8020`).
The cumulative ACK therefore remains: `Ack=8011` (The first missing byte is 8011).

---
### Part 5: Selective Acknowledgment

## 22. What SACK Adds
A normal cumulative ACK tells the sender only: "I received everything before byte 8011."
SACK provides additional information about later ranges that were received.

The client can send:
- ACK flag = 1
- Ack = 8011
- SACK block = 8021–8041

**Conceptually, this means:**
- **Cumulative ACK:** I received everything before byte 8011.
- **Missing:** 8011–8020
- **SACK information:** I already received bytes 8021–8040. (SACK block 8021–8041 means bytes 8021–8040 were received. The SACK upper boundary is commonly represented as the byte after the received range).

## 23. SACK Diagram
```text
CLIENT                                             SERVER
                                                Segment 1
                                                 Seq=8001
                                          Bytes=8001–8010
<----------------------------------------------------
ACK
Ack=8011
---------------------------------------------------->

                                                Segment 2
                                                 Seq=8011
                                          Bytes=8011–8020
<------------------------- X LOST

                                                Segment 3
                                                 Seq=8021
                                          Bytes=8021–8030
<----------------------------------------------------
ACK
Ack=8011
SACK=8021–8031
---------------------------------------------------->

                                                Segment 4
                                                 Seq=8031
                                          Bytes=8031–8040
<----------------------------------------------------
ACK
Ack=8011
SACK=8021–8041
---------------------------------------------------->
```
The server can now determine:
- Received: 8001–8010, 8021–8040
- Missing: 8011–8020

## 24. Server Retransmits Only the Missing Range
The server retransmits segment 2:
**SERVER → CLIENT**
- Seq = 8011
- Payload length = 10 bytes
- Payload = "a reliable"

```text
CLIENT                                             SERVER
                                           RETRANSMISSION
                                                 Seq=8011
                                                Length=10
                                        Data="a reliable"
<----------------------------------------------------
```
The server does not need to resend segments 3 and 4 because SACK showed that the client already received them.

## 25. Client Can Now Reassemble Everything
After receiving the retransmitted segment, the client has:
- 8001–8010 "TCP sends "
- 8011–8020 "a reliable"
- 8021–8030 " ordered b"
- 8031–8040 "yte stream."

The complete ordered stream becomes: `TCP sends a reliable ordered byte stream.`
The client can now deliver the complete data to the application.

## 26. Client Sends the Final ACK
The client now has every byte through 8040.
It sends:
**CLIENT → SERVER**
- Seq = 5001
- Ack = 8041
- ACK flag = 1

```text
CLIENT                                             SERVER
ACK=1
Seq=5001
Ack=8041
---------------------------------------------------->
```
**Meaning:** I received every byte through 8040. The next server byte I expect is 8041.

---
### Part 6: Full Transfer Diagram
```text
CLIENT                                             SERVER
             CONNECTION ESTABLISHMENT
SYN
Seq=5000
---------------------------------------------------->
                                              SYN+ACK
                                             Seq=8000
                                             Ack=5001
<----------------------------------------------------
ACK
Seq=5001
Ack=8001
---------------------------------------------------->

                SERVER SENDS DATA
                                            Segment 1
                                             Seq=8001
                                            Length=10
                                    Data="TCP sends "
<----------------------------------------------------
ACK
Ack=8011
---------------------------------------------------->

                                            Segment 2
                                             Seq=8011
                                            Length=10
                                    Data="a reliable"
<------------------------- X LOST

                                            Segment 3
                                             Seq=8021
                                            Length=10
                                    Data=" ordered b"
<----------------------------------------------------
ACK
Ack=8011
SACK=8021–8031
---------------------------------------------------->

                                            Segment 4
                                             Seq=8031
                                            Length=10
                                    Data="yte stream."
<----------------------------------------------------
ACK
Ack=8011
SACK=8021–8041
---------------------------------------------------->

                  LOSS RECOVERY
                              Retransmitted Segment 2
                                             Seq=8011
                                            Length=10
                                    Data="a reliable"
<----------------------------------------------------
ACK
Seq=5001
Ack=8041
---------------------------------------------------->

             COMPLETE APPLICATION DATA
     "TCP sends a reliable ordered byte stream."
```

---
### Part 7: Bidirectional Data Example

## 27. Client Sends "OK" Back to the Server
After receiving the paragraph, suppose the client sends: `OK`
- "O" = 1 byte
- "K" = 1 byte
- Total = 2 bytes

The client's current sequence number is: `5001`.
It sends:
**CLIENT → SERVER**
- Seq = 5001
- Ack = 8041
- ACK flag = 1
- Payload length = 2
- Payload = "OK"

```text
CLIENT                                             SERVER
Seq=5001
Ack=8041
Length=2
Data="OK"
---------------------------------------------------->
```
**Meaning of Seq=5001:** The client's outgoing data begins at client byte 5001.
**Meaning of Ack=8041:** The client has received every server byte through 8040.
The client bytes are: "O" = sequence 5001, "K" = sequence 5002.
Therefore, the next client sequence number is: `5001 + 2 = 5003`.

## 28. Server Acknowledges "OK"
The server sends:
**SERVER → CLIENT**
- Seq = 8041
- Ack = 5003
- ACK flag = 1
- Payload = none

```text
CLIENT                                             SERVER
                                                ACK=1
                                             Seq=8041
                                             Ack=5003
<----------------------------------------------------
```
**Meaning of Ack=5003:** I received client bytes 5001 and 5002. The next client byte I expect is 5003.

---
### Part 8: How TCP Knows What an ACK Refers To

## 29. Each ACK Refers to the Opposite Direction
Suppose the client sends:
- Seq=5001
- Ack=8041
- Payload="OK"

These values describe two independent streams:
- **Seq=5001:** My client data begins at client byte 5001.
- **Ack=8041:** I received server data through server byte 8040.

The sequence number always describes the sender's outgoing byte stream. The acknowledgment number always describes the other endpoint's byte stream.

## 30. Visual Model of Two Independent Streams
**CLIENT-TO-SERVER STREAM**
Client bytes: `5001 5002 5003 5004 ...` -> `O K`
Server acknowledges client data using: `Ack=5003`

**SERVER-TO-CLIENT STREAM**
Server bytes: `8001 8002 ... 8040 8041 ...` -> `T C .`
Client acknowledges server data using: `Ack=8041`

---
### Part 9: Core Formulas

## 31. Normal Data
`Next Seq = Current Seq + Payload Length`
- Example: Current Seq = 8001, Payload length = 10. Next Seq = 8011.

`Ack = Received Seq + Received Payload Length`
- Example: Received Seq = 8001, Payload length = 10. Ack = 8011.

## 32. SYN
SYN consumes one sequence number: `Ack = SYN Seq + 1`
- Example: SYN Seq = 5000. Ack = 5001.

## 33. FIN
FIN also consumes one sequence number: `Ack = FIN Seq + 1`

## 34. ACK Without Data
A pure ACK normally does not consume sequence-number space.
- Example: Seq = 5001, Ack = 8041, Payload = 0 bytes. Next client Seq remains 5001.

*The ACK flag itself is not a phantom byte. The SYN and FIN control flags consume sequence numbers.*

---
### Part 10: Flags, Fields, and State Variables

## 35. TCP Flags
Flags are one-bit control values:
- **SYN** = Start and synchronize a connection
- **ACK** = Acknowledgment-number field is valid
- **FIN** = Sender has finished sending
- **RST** = Immediately reset the connection
- **PSH** = Request prompt delivery to the application

Example: `SYN=1, ACK=1` means both SYN and ACK are active in the same TCP segment.

## 36. TCP Header Fields
These are numeric values transmitted inside the TCP header:
- Source Port
- Destination Port
- Sequence Number
- Acknowledgment Number
- Receive Window
- Checksum

## 37. Internal TCP State Variables
Some TCP values are maintained internally by the operating system:
- **RTT** = Estimated round-trip time
- **cwnd** = Congestion window
- **RTO** = Retransmission timeout

The effective amount of unacknowledged data is limited approximately by: `minimum(rwnd, cwnd)`
- **rwnd:** How much receive-buffer capacity the receiver advertises.
- **cwnd:** How much data the sender believes the network can currently handle.

---
### Part 11: Final Permanent-Memory Model

- TCP creates one reliable, ordered, bidirectional byte stream.
- A TCP connection has two independent sequence-number spaces (Client-to-server and Server-to-client).
- **Seq** means: "My outgoing payload begins at this byte position."
- **Ack** means: "I received all bytes from you before this number. This is the next byte I expect."
- **SYN** consumes one sequence number.
- **ACK** itself does not consume a sequence number.
- Normal application data consumes sequence numbers according to the number of payload bytes.
- TCP can send multiple segments before waiting for ACKs because it uses a sliding window.
- TCP ACKs are cumulative: `Ack=N` means all bytes before N were received in order.
- If data is missing, the cumulative ACK remains at the first missing byte.
- Duplicate ACKs indicate that later data may have arrived while an earlier byte range is still missing.
- **SACK** adds information about later byte ranges that arrived successfully. With SACK, the sender can retransmit only the missing ranges instead of retransmitting data that the receiver already has.

**One-Line Summary:** Sequence numbers identify where outgoing bytes belong, while acknowledgment numbers identify the next byte expected from the opposite endpoint.
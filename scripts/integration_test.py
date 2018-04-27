from ethereum import utils

token1 = 'fjDy8vAdvHE:APA91bHGE51C3j0OJz6fBuRUwa_aV1pLzVCh3vePVA4h2-9nhTbz4-gy6KIcduMs3PGncPAryNQ0VxyF7z3KdKviD10_yNGzgzVkXhdNQ7OWlxYgEaIorXXYkPPe45aUR4C0ic2aYSIw'
priv1 = bytes.fromhex('17fa8dab3ff55ca2156a47a0f128e67789a3a2da6adebf581e1c4c2f99fbc071')
address1 = '0x919aff0cc2975DEB38379a65FB2Debc6c6CdF028'

token2 = 'fWU_G7outKU:APA91bF4BiMJt1eiknSKzThEx6Fs7u1ZkXDbDPGcYPcaS6Nm2pfegfaDKcaHxGmKMOK8vXEWp8bZD1Z8KmMgbpGQXaVsSNoG0BascdUZhDqcngvQGqHmByurg7ShVb6XYFc5YVxAhETT'
priv2 = bytes.fromhex('0a3c393c83a0c45d6509419980c2828bbb129ed2ff966abebda9d7157ffa8e9c')
address2 = '0x2865BE1F71ddA04FC9A596fA70a7Db4F82890343'

prefix = 'GNO'

v1, r1, s1, = utils.ecsign(utils.sha3(prefix + token1), priv1)
print("=== 1 ===")
print("R: %s" % r1)
print("S: %s" % s1)
print("V: %s" % v1)

v2, r2, s2, = utils.ecsign(utils.sha3(prefix + token2), priv2)
print("=== 2 ===")
print("R: %s" % r2)
print("S: %s" % s2)
print("V: %s" % v2)

print("=== Message ===")
v_mess2, r_mess2, s_mess2, = utils.ecsign(utils.sha3(prefix + "{\"title\":\"Hello Patron\"}"), priv2)
print("R: %s" % r_mess2)
print("S: %s" % s_mess2)
print("V: %s" % v_mess2)
